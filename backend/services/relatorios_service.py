"""Camada de serviço para operações de Relatórios Técnicos."""
from __future__ import annotations

from datetime import date, datetime
from flask import request
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models import Aluno, Relatorio, Usuario
from backend.services.audit import registrar_atividade


def serializar_relatorio(relatorio: Relatorio) -> dict:
    """Converte um objeto Relatorio em dict para resposta JSON."""
    tipo_fe = relatorio.tipo
    if tipo_fe == 'psicopedagogico':
        titulo_l = (relatorio.titulo or '').lower()
        conteudo_l = (relatorio.conteudo or '').lower()
        if 'laudo' in titulo_l or 'laudo' in conteudo_l:
            tipo_fe = 'laudo'
        else:
            tipo_fe = 'parecer'
            
    status_fe = relatorio.status
    if status_fe == 'publicado':
        status_fe = 'emitido'

    return {
        'id': relatorio.id,
        'unidade_id': relatorio.unidade_id,
        'unidade_nome': relatorio.unidade.nome if relatorio.unidade else None,
        'aluno_id': relatorio.aluno_id,
        'aluno_nome': relatorio.aluno.nome_completo if relatorio.aluno else None,
        'autor_id': relatorio.autor_id,
        'autor_nome': relatorio.autor.nome_completo if relatorio.autor else None,
        'tipo': tipo_fe,
        'origem': relatorio.origem,
        'ano_referencia': relatorio.ano_referencia,
        'periodo_inicio': relatorio.periodo_inicio.isoformat() if relatorio.periodo_inicio else None,
        'periodo_fim': relatorio.periodo_fim.isoformat() if relatorio.periodo_fim else None,
        'titulo': relatorio.titulo,
        'conteudo': relatorio.conteudo,
        'status': status_fe,
        'created_at': relatorio.created_at.isoformat() if relatorio.created_at else None,
        'updated_at': relatorio.updated_at.isoformat() if relatorio.updated_at else None,
    }


def criar_relatorio_service(payload: dict, autor_id: int) -> Relatorio:
    """Cria um novo relatório técnico ou parecer pedagógico."""
    aluno = Aluno.query.get_or_404(payload['aluno_id'])
    autor = Usuario.query.get_or_404(autor_id)

    # Validação multi-tenant: O aluno deve pertencer à mesma unidade do autor
    if autor.perfil and autor.perfil.nome != 'administrador':
        if aluno.unidade_id != autor.unidade_id:
            raise ValueError('O aluno selecionado não pertence à sua unidade escolar.')

    p_ini = None
    if payload.get('periodo_inicio'):
        p_ini = date.fromisoformat(payload['periodo_inicio'])

    p_fim = None
    if payload.get('periodo_fim'):
        p_fim = date.fromisoformat(payload['periodo_fim'])

    tipo_db = payload['tipo'].strip()
    if tipo_db in ('parecer', 'laudo'):
        tipo_db = 'psicopedagogico'

    status_db = payload.get('status', 'rascunho').strip()
    if status_db == 'emitido':
        status_db = 'publicado'

    relatorio = Relatorio(
        unidade_id=aluno.unidade_id,
        aluno_id=payload['aluno_id'],
        autor_id=autor_id,
        tipo=tipo_db,
        origem='manual',
        ano_referencia=payload.get('ano_referencia'),
        periodo_inicio=p_ini,
        periodo_fim=p_fim,
        titulo=payload['titulo'].strip(),
        conteudo=payload.get('conteudo', '').strip() or None,
        status=status_db,
    )

    db.session.add(relatorio)
    db.session.commit()
    return relatorio


def buscar_relatorio_service(relatorio_id: int, unidade_id: int | None = None) -> Relatorio:
    """Busca um relatório por ID e valida multi-tenant se unidade_id for fornecido."""
    relatorio = Relatorio.query.get_or_404(relatorio_id)
    if unidade_id and relatorio.unidade_id != unidade_id:
        raise ValueError('Acesso não autorizado a este relatório.')
    return relatorio


def listar_relatorios_service(
    autor_id: int | None,
    status: str | None,
    q: str,
    page: int,
    limit: int,
    unidade_id: int | None = None,
) -> dict:
    """Lista relatórios com paginação, filtros e controle multi-tenant."""
    query = (
        Relatorio.query
        .join(Aluno, Relatorio.aluno_id == Aluno.id)
        .join(Usuario, Relatorio.autor_id == Usuario.id)
    )

    if autor_id:
        query = query.filter(Relatorio.autor_id == autor_id)

    if unidade_id:
        query = query.filter(Relatorio.unidade_id == unidade_id)

    if status:
        status_db = status
        if status_db == 'emitido':
            status_db = 'publicado'
        query = query.filter(Relatorio.status == status_db)

    if q:
        termo = f'%{q.lower()}%'
        query = query.filter(
            or_(
                func.lower(Aluno.nome_completo).like(termo),
                func.lower(Relatorio.titulo).like(termo),
                func.lower(Relatorio.conteudo).like(termo),
            )
        )

    total = query.count()
    relatorios = (
        query
        .order_by(Relatorio.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        'items': [serializar_relatorio(r) for r in relatorios],
        'total': total,
        'page': page,
        'limit': limit,
    }


def obter_dashboard_relatorios_service(unidade_id: int | None = None) -> dict:
    """Retorna contadores de relatórios por unidade."""
    query_base = Relatorio.query

    if unidade_id:
        query_base = query_base.filter(Relatorio.unidade_id == unidade_id)

    total = query_base.count()
    emitidos = query_base.filter(Relatorio.status == 'publicado').count()
    rascunhos = query_base.filter(Relatorio.status == 'rascunho').count()

    return {
        'total': total,
        'emitidos': emitidos,
        'rascunhos': rascunhos,
    }


def registrar_atividade_relatorio(usuario_id: int, acao: str, relatorio: Relatorio) -> None:
    """Registra ação de auditoria para relatório técnico."""
    registrar_atividade(
        usuario_id,
        acao,
        'relatorio',
        relatorio.id,
        detalhes={
            'aluno_id': relatorio.aluno_id,
            'titulo': relatorio.titulo,
            'status': relatorio.status,
        },
        ip_origem=request.headers.get('X-Forwarded-For', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
    )
    db.session.commit()
