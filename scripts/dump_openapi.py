import yaml
import sys
import os

# Asegurar que la ruta base esté en sys.path para poder importar 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

def dump():
    """
    Exporta la configuración actual de OpenAPI generada por FastAPI
    y la guarda en el archivo openapi.yaml en la raíz del proyecto.
    
    Este script debe ejecutarse cada vez que se agregue o modifique un endpoint
    o un esquema Pydantic, para mantener el contrato oficial actualizado.
    
    Ejecución manual: python scripts/dump_openapi.py
    """
    print("Generando esquema OpenAPI desde FastAPI...")
    openapi_schema = app.openapi()
    
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'openapi.yaml'))
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, sort_keys=False, allow_unicode=True)
        
    print(f"[EXITO] Esquema OpenAPI exportado exitosamente a: {output_path}")

if __name__ == "__main__":
    dump()
