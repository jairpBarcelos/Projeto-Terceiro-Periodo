import pathlib
html = pathlib.Path('frontend/pages/menus/psicopedagogo/triagensAvaliacoes.html').read_text(encoding='utf-8')
print('Total linhas:', html.count('\n'))
print('modalEditTriagem:', 'modalEditTriagem' in html)
print('abrirEditTriagem:', 'abrirEditTriagem' in html)
print('triagem-card:', 'triagem-card' in html)
print('PUT triagens:', 'PUT' in html)
# Find the triagens render section
marker = "getElementById('hist-triagens-body')"
idx = html.find(marker)
print('hist-triagens-body JS pos:', idx)
if idx >= 0:
    print('Snippet:', repr(html[idx:idx+120]))
