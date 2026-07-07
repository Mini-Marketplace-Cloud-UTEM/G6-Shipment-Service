import markdown
import codecs
import sys

def convert():
    try:
        with codecs.open('docs/Auditoria_Integraciones.md', mode='r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        with codecs.open('docs/Auditoria_Integraciones.md', mode='r', encoding='latin-1') as f:
            text = f.read()
            
    html = markdown.markdown(text, extensions=['tables'])
    full_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Auditoria de Integraciones</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; max-width: 800px; margin: auto; }}
            h1, h2, h3 {{ color: #333; }}
            pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    '''
    
    with codecs.open('docs/Auditoria_Integraciones.html', mode='w', encoding='utf-8') as f:
        f.write(full_html)

if __name__ == '__main__':
    convert()
