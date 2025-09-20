from fastapi import FastAPI, HTTPException, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from urllib.parse import quote_plus
import os

# Configuración de la base de datos usando variables de entorno separadas
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Construir DATABASE_URL desde variables individuales
    DB_HOST = os.getenv("DB_HOST", "20.84.99.214")
    DB_PORT = os.getenv("DB_PORT", "443")
    DB_NAME = os.getenv("DB_NAME", "jf100124")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "uPxBHn]Ag9H~N4'K")
    
    # Codificar la contraseña para la URL
    ENCODED_PASSWORD = quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuración de la base de datos con SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Definir el modelo de la base de datos
class Estudiante(Base):
    __tablename__ = "estudiantes"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), index=True)
    edad = Column(Integer)

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# Esquema Pydantic para validación de datos
class EstudianteSchema(BaseModel):
    nombre: str
    edad: int

# Instancia de la aplicación FastAPI
app = FastAPI(
    title="API de Estudiantes",
    description="API para gestionar estudiantes",
    version="1.0.0"
)

# CORS configuración mejorada
origins = [
    "http://localhost:3000",
    "http://localhost:8080", 
    "https://localhost:3000",
    "https://localhost:8080",
    "*"  # En producción, especifica dominios específicos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Dependency para la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ruta de salud para verificar que el servicio está funcionando
@app.get("/")
def root():
    return {
        "message": "API de Estudiantes funcionando correctamente", 
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Rutas de la API

@app.get("/estudiantes/")
def get_estudiantes(db: Session = Depends(get_db)):
    try:
        estudiantes = db.query(Estudiante).all()
        return {
            "data": [
                {"id": est.id, "nombre": est.nombre, "edad": est.edad}
                for est in estudiantes
            ],
            "count": len(estudiantes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes: {str(e)}")

@app.get("/estudiantes/{id}")
def get_estudiante(id: int, db: Session = Depends(get_db)):
    try:
        estudiante = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return {"id": estudiante.id, "nombre": estudiante.nombre, "edad": estudiante.edad}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")

@app.post("/estudiantes/")
def crear_estudiante(estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    try:
        db_estudiante = Estudiante(nombre=estudiante.nombre, edad=estudiante.edad)
        db.add(db_estudiante)
        db.commit()
        db.refresh(db_estudiante)
        return {
            "mensaje": "Estudiante creado exitosamente.",
            "estudiante": {
                "id": db_estudiante.id, 
                "nombre": db_estudiante.nombre, 
                "edad": db_estudiante.edad
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

@app.put("/estudiantes/{id}")
def modificar_estudiante(id: int, estudiante: EstudianteSchema, db: Session = Depends(get_db)):
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        est.nombre = estudiante.nombre
        est.edad = estudiante.edad
        db.commit()
        db.refresh(est)
        return {
            "mensaje": "Estudiante actualizado exitosamente",
            "data": {"id": est.id, "nombre": est.nombre, "edad": est.edad}
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")

@app.delete("/estudiantes/{id}")
def eliminar_estudiante(id: int, db: Session = Depends(get_db)):
    try:
        est = db.query(Estudiante).filter(Estudiante.id == id).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        db.delete(est)
        db.commit()
        return {"mensaje": "Estudiante eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")

# Solo para desarrollo local
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Configurar reload solo en desarrollo
    reload = environment == "development"
    
    print(f"Iniciando servidor en puerto {port}")
    print(f"Entorno: {environment}")
    print(f"Reload activado: {reload}")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)