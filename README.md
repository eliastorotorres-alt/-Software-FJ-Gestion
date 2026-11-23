# Software FJ – Gestión de Clientes, Servicios y Reservas

## Descripción
Aplicación en **Python** (programación orientada a objetos, **sin base de datos**) para la empresa ficticia *Software FJ*. Gestiona clientes, servicios (reserva de salas, alquiler de equipos y asesorías especializadas) y reservas, con **manejo robusto de excepciones**: ningún error detiene el programa y todos quedan registrados en un archivo de logs.

Proyecto de la **Fase 4 – Componente práctico simulado** del curso Programación (213023), UNAD.

## Funcionalidades
- Registro de clientes con validación de nombre, documento, correo y teléfono.
- Creación de tres tipos de servicio y activación / desactivación de cada uno.
- Cálculo de costos con impuestos y descuentos (sobrecarga de métodos).
- Creación, confirmación, procesamiento y cancelación de reservas.
- Interfaz gráfica con pestañas: Clientes, Servicios, Reservas, Simulación y Registros.
- Simulación de **18 operaciones** (válidas e inválidas) que demuestra que el sistema sigue funcionando ante errores.
- Archivo de logs en `logs/software_fj.log`.

## Conceptos aplicados
| Concepto | Dónde |
|---|---|
| Abstracción | `EntidadBase` y `Servicio` (clases abstractas) |
| Herencia | `Cliente`, `Servicio`, `Reserva`; `ReservaSala`, `AlquilerEquipo`, `AsesoriaEspecializada` |
| Polimorfismo | `describir()`, `validar_parametros()` y `_recargo()` sobrescritos en cada servicio |
| Encapsulación | Atributos privados con propiedades y validación en `Cliente` |
| Sobrecarga | `calcular_costo(h, impuesto, descuento)`, `calcular_costo_con_iva(h)`, `cotizar(h, *extras)` |
| Excepciones | Jerarquía propia (`SoftwareFJError`), `try/except`, `try/except/else`, `try/except/finally`, encadenamiento con `raise ... from` |

## Estructura del repositorio
```text
software-fj-grupo-213023/
├── logs/                 # aquí se genera software_fj.log
├── .gitattributes
├── .gitignore
├── EJECUTAR.bat          # lanzador para Windows (no se cierra solo)
├── README.md
└── software_fj.py        # programa completo
```

## Requisitos
- Python 3.8 o superior (Tkinter viene incluido en Windows y Mac).
- No requiere instalar paquetes con `pip`.

Verificar Python y Tkinter:
```powershell
python --version
python -m tkinter
```

## Ejecución
```powershell
git clone URL_DEL_REPOSITORIO
cd software-fj-grupo-213023
python software_fj.py             # interfaz gráfica
python software_fj.py --consola   # simulación en consola
```
En Windows también basta con hacer doble clic en `EJECUTAR.bat`.

## Trabajo colaborativo en GitHub
| Integrante | Rama de trabajo | Aporte |
|---|---|---|
| [Integrante 1] | `integrante1_fase4` | Logs y excepciones (secciones 1 y 2) |
| [Integrante 2] | `integrante2_fase4` | Entidad base y Cliente (sección 3) |
| [Integrante 3] | `integrante3_fase4` | Servicios (sección 4) |
| [Integrante 4] | `integrante4_fase4` | Reserva y gestor (sección 5) |
| [Integrante 5] | `integrante5_fase4` | Simulación e interfaz (secciones 6 y 7) |

Comandos básicos:
```bash
git checkout -b integrante1_fase4     # crear y cambiar a tu rama
git add .                             # preparar cambios
git commit -m "Describe tu cambio"    # guardar cambios
git push origin integrante1_fase4     # subir tu rama
git pull origin main                  # traer cambios del equipo
git merge integrante1_fase4           # integrar ramas (o usar Pull Request)
```

---
**UNAD – Universidad Nacional Abierta y a Distancia**
Curso: Programación (213023) · Grupo: 213023_[NÚMERO] · Actividad: Fase 4
