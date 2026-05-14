from __future__ import annotations

from backend.extensions import db
from backend.models import AnoLetivo
from backend.responses import error
from flask import current_app

def listar_anos_letivos_service():
    anos = AnoLetivo.query.order_by(AnoLetivo.ano.desc()).all()
    return [serializar_ano_letivo(a) for a in anos]

def criar_ano_letivo_service(data: dict):
    ano_val = data.get('ano')
    if not ano_val:
        return error('O campo ano é obrigatório.', 400)
    
    if AnoLetivo.query.filter_by(ano=ano_val).first():
        return error(f'O ano letivo {ano_val} já está cadastrado.', 400)
    
    # Se o novo ano for ativo, desativar outros se necessário? 
    # Por enquanto, permite múltiplos ativos.
    
    novo_ano = AnoLetivo(
        ano=ano_val,
        status=data.get('status', 'ativo'),
        data_inicio=data.get('data_inicio'),
        data_fim=data.get('data_fim')
    )
    
    db.session.add(novo_ano)
    db.session.commit()
    
    return serializar_ano_letivo(novo_ano)

def atualizar_ano_letivo_service(ano_id: int, data: dict):
    ano = AnoLetivo.query.get_or_404(ano_id)
    
    if 'ano' in data:
        existente = AnoLetivo.query.filter(AnoLetivo.ano == data['ano'], AnoLetivo.id != ano_id).first()
        if existente:
            return error(f'O ano letivo {data["ano"]} já está cadastrado.', 400)
        ano.ano = data['ano']
    
    if 'status' in data:
        ano.status = data['status']
    if 'data_inicio' in data:
        ano.data_inicio = data['data_inicio']
    if 'data_fim' in data:
        ano.data_fim = data['data_fim']
        
    db.session.commit()
    return serializar_ano_letivo(ano)

def remover_ano_letivo_service(ano_id: int):
    ano = AnoLetivo.query.get_or_404(ano_id)
    db.session.delete(ano)
    db.session.commit()
    return True

def serializar_ano_letivo(ano: AnoLetivo):
    return {
        'id': ano.id,
        'ano': ano.ano,
        'status': ano.status,
        'data_inicio': ano.data_inicio.isoformat() if ano.data_inicio else None,
        'data_fim': ano.data_fim.isoformat() if ano.data_fim else None,
        'created_at': ano.created_at.isoformat(),
        'updated_at': ano.updated_at.isoformat()
    }
