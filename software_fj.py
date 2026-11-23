"""
UNAD:       Universidad Nacional Abierta y a Distancia
ECBTI:      Escuela de Ciencias Básicas, Tecnología e Ingeniería
Curso:      Programación (213023)
Grupo:      213023_[NÚMERO DE GRUPO]
Programa:   Ingeniería de Sistemas

Actividad:  Fase 4 - Componente práctico simulado
Proyecto:   Software FJ - Sistema Integral de Gestión de Clientes,
            Servicios y Reservas (sin base de datos)
Autores:    [Integrante 1], [Integrante 2], [Integrante 3],
            [Integrante 4], [Integrante 5]
Versión:    1.0

Ejecución:
    python software_fj.py             -> abre la interfaz gráfica
    python software_fj.py --consola   -> ejecuta la simulación en consola
"""
from __future__ import annotations

import logging
import re
import sys
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from itertools import count
from pathlib import Path

try:                                    # La interfaz gráfica es opcional:
    import tkinter as tk                # si Tkinter no existe, el programa
    from tkinter import messagebox, ttk  # sigue funcionando en modo consola.
except ImportError:                     # pragma: no cover
    tk = None


# ============================================================================
# SECCIÓN 1: ARCHIVO DE LOGS
# Responsable: [Integrante 1]
# Registra TODOS los eventos y errores en logs/software_fj.log
# (el archivo se usa solo para registro; no es una base de datos).
# ============================================================================
CARPETA_LOGS = Path(__file__).resolve().parent / "logs"
ARCHIVO_LOG = CARPETA_LOGS / "software_fj.log"

log = logging.getLogger("SoftwareFJ")
log.setLevel(logging.INFO)
if not log.handlers:
    try:
        CARPETA_LOGS.mkdir(exist_ok=True)
        _manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    except OSError:
        # Si no se puede escribir el archivo, el sistema NO se detiene.
        _manejador = logging.StreamHandler()
    _manejador.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    log.addHandler(_manejador)


# ============================================================================
# SECCIÓN 2: EXCEPCIONES PERSONALIZADAS
# Responsable: [Integrante 1]
# Todas heredan de SoftwareFJError: se puede capturar "cualquier error del
# dominio" con un solo except o atender cada tipo por separado.
# ============================================================================
class SoftwareFJError(Exception):
    """Excepción base del sistema."""


class ClienteInvalidoError(SoftwareFJError):
    """Datos del cliente inválidos."""


class ParametroFaltanteError(SoftwareFJError):
    """Falta un parámetro obligatorio."""


class ParametroInvalidoError(SoftwareFJError):
    """Un parámetro tiene un formato o tipo incorrecto."""


class ServicioInvalidoError(SoftwareFJError):
    """Parámetros de un servicio inválidos."""


class ServicioNoDisponibleError(SoftwareFJError):
    """El servicio existe pero no está disponible."""


class ReservaInvalidaError(SoftwareFJError):
    """Intento de reserva incorrecto."""


class OperacionNoPermitidaError(SoftwareFJError):
    """Operación no válida para el estado actual."""


class CalculoInconsistenteError(SoftwareFJError):
    """El cálculo de costos produjo valores inconsistentes."""


def numero(texto, campo: str, entero: bool = False):
    """Convierte texto a número; lanza excepciones propias si no se puede."""
    texto = str(texto).strip().replace(",", ".")
    if not texto:
        raise ParametroFaltanteError(f"Falta el campo '{campo}'.")
    try:
        return int(texto) if entero else float(texto)
    except ValueError as error:
        tipo = "un número entero" if entero else "un número"
        # Encadenamiento: se conserva el error original (from error)
        raise ParametroInvalidoError(
            f"'{campo}' debe ser {tipo}: {texto!r}") from error


# ============================================================================
# SECCIÓN 3: ENTIDAD BASE (abstracta) Y CLIENTE
# Responsable: [Integrante 2]
# Abstracción + encapsulación (atributos privados con validación).
# ============================================================================
class EntidadBase(ABC):
    """Abstracción de cualquier entidad del sistema."""

    _familia = "entidad"
    _contadores: dict = {}

    def __init__(self) -> None:
        contador = EntidadBase._contadores.setdefault(self._familia, count(1))
        self._id = next(contador)
        self._fecha_creacion = datetime.now()

    @property
    def id(self) -> int:
        return self._id

    @property
    def fecha_creacion(self) -> datetime:
        return self._fecha_creacion

    @abstractmethod
    def describir(self) -> str:
        """Cada entidad debe poder describirse en texto."""

    def __str__(self) -> str:
        return self.describir()


class Cliente(EntidadBase):
    """Cliente con datos personales encapsulados y validados."""

    _familia = "cliente"
    _PATRON_EMAIL = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

    def __init__(self, nombre=None, email=None, telefono=None,
                 documento=None) -> None:
        datos = {"nombre": nombre, "email": email, "telefono": telefono,
                 "documento": documento}
        faltantes = [k for k, v in datos.items()
                     if v is None or (isinstance(v, str) and not v.strip())]
        if faltantes:
            raise ParametroFaltanteError(
                "Faltan datos del cliente: " + ", ".join(faltantes))
        # Los setters validan; si alguno falla no se crea el objeto
        self.nombre, self.email = nombre, email
        self.telefono, self.documento = telefono, documento
        super().__init__()

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor) -> None:
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ClienteInvalidoError(
                "El nombre debe tener al menos 3 caracteres.")
        if any(c.isdigit() for c in valor):
            raise ClienteInvalidoError("El nombre no puede contener números.")
        self.__nombre = valor.strip().title()

    @property
    def email(self) -> str:
        return self.__email

    @email.setter
    def email(self, valor) -> None:
        if not isinstance(valor, str) or not self._PATRON_EMAIL.match(valor.strip()):
            raise ClienteInvalidoError(f"Correo inválido: {valor!r}")
        self.__email = valor.strip().lower()

    @property
    def telefono(self) -> str:
        return self.__telefono

    @telefono.setter
    def telefono(self, valor) -> None:
        if not isinstance(valor, str) or not valor.strip().isdigit() \
                or not 7 <= len(valor.strip()) <= 10:
            raise ClienteInvalidoError(
                f"Teléfono inválido (7 a 10 dígitos): {valor!r}")
        self.__telefono = valor.strip()

    @property
    def documento(self) -> str:
        return self.__documento

    @documento.setter
    def documento(self, valor) -> None:
        if not isinstance(valor, str) or not valor.strip().isdigit() \
                or not 5 <= len(valor.strip()) <= 12:
            raise ClienteInvalidoError(
                f"Documento inválido (5 a 12 dígitos): {valor!r}")
        self.__documento = valor.strip()

    def describir(self) -> str:
        return (f"Cliente #{self.id}: {self.nombre} | Doc: {self.documento} | "
                f"{self.email} | Tel: {self.telefono}")


# ============================================================================
# SECCIÓN 4: SERVICIOS (clase abstracta + 3 especializados)
# Responsable: [Integrante 3]
# Herencia, polimorfismo (métodos sobrescritos) y sobrecarga de métodos.
# ============================================================================
IVA = 0.19


class Servicio(EntidadBase):
    """Clase abstracta de servicio."""

    _familia = "servicio"
    tipo = "Servicio"

    def __init__(self, nombre=None, tarifa_hora=None) -> None:
        if nombre is None or tarifa_hora is None:
            raise ParametroFaltanteError(
                "Todo servicio requiere 'nombre' y 'tarifa_hora'.")
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("Nombre de servicio inválido.")
        if isinstance(tarifa_hora, bool) or \
                not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError(
                f"La tarifa por hora debe ser positiva: {tarifa_hora!r}")
        super().__init__()
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)
        self._disponible = True

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_hora(self) -> float:
        return self._tarifa_hora

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, valor: bool) -> None:
        if not isinstance(valor, bool):
            raise ServicioInvalidoError("'disponible' debe ser True o False.")
        self._disponible = valor

    @abstractmethod
    def validar_parametros(self, horas) -> None:
        """Valida la duración según el servicio concreto."""

    @abstractmethod
    def _recargo(self) -> float:
        """Factor multiplicador propio de cada servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Descripción propia de cada servicio."""

    # --- Sobrecarga: varias formas de calcular el costo -------------------
    def calcular_costo(self, horas, impuesto: float = 0.0,
                       descuento: float = 0.0) -> float:
        """calcular_costo(h) | (h, impuesto) | (h, impuesto, descuento)."""
        self.validar_parametros(horas)
        if not 0 <= impuesto <= 1:
            raise CalculoInconsistenteError(
                f"Impuesto fuera de rango [0 a 100 %]: {impuesto * 100:.0f} %")
        if not 0 <= descuento <= 0.5:
            raise CalculoInconsistenteError(
                f"Descuento fuera de rango [0 a 50 %]: {descuento * 100:.0f} %")
        total = self._tarifa_hora * horas * self._recargo() \
            * (1 - descuento) * (1 + impuesto)
        if total <= 0:
            raise CalculoInconsistenteError(f"Costo inconsistente: {total}")
        return round(total, 2)

    def calcular_costo_con_iva(self, horas) -> float:
        """Variante: costo con IVA estándar (19 %)."""
        return self.calcular_costo(horas, impuesto=IVA)

    def cotizar(self, horas, *extras) -> float:
        """Sobrecarga por cantidad de argumentos:
        cotizar(h) | cotizar(h, impuesto) | cotizar(h, impuesto, descuento)."""
        if len(extras) > 2:
            raise ParametroInvalidoError("cotizar admite hasta 2 extras.")
        return self.calcular_costo(horas, *extras)


class ReservaSala(Servicio):
    tipo = "Sala"

    def __init__(self, nombre=None, tarifa_hora=None, capacidad=None):
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) \
                or capacidad < 1:
            raise ServicioInvalidoError(f"Capacidad inválida: {capacidad!r}")
        super().__init__(nombre, tarifa_hora)
        self._capacidad = capacidad

    def validar_parametros(self, horas) -> None:
        if not isinstance(horas, (int, float)) or not 1 <= horas <= 8:
            raise ServicioInvalidoError("Una sala se reserva de 1 a 8 horas.")

    def _recargo(self) -> float:
        return 1.2 if self._capacidad > 20 else 1.0     # salas grandes +20 %

    def describir(self) -> str:
        return (f"Sala '{self.nombre}' (capacidad {self._capacidad}) - "
                f"${self.tarifa_hora:,.0f}/h")


class AlquilerEquipo(Servicio):
    tipo = "Equipo"

    def __init__(self, nombre=None, tarifa_hora=None, tipo_equipo=None,
                 requiere_deposito=False):
        if not isinstance(tipo_equipo, str) or not tipo_equipo.strip():
            raise ServicioInvalidoError("Debe indicar el tipo de equipo.")
        super().__init__(nombre, tarifa_hora)
        self._tipo_equipo = tipo_equipo.strip()
        self._requiere_deposito = bool(requiere_deposito)

    def validar_parametros(self, horas) -> None:
        if not isinstance(horas, (int, float)) or not 1 <= horas <= 72:
            raise ServicioInvalidoError(
                "Un equipo se alquila de 1 a 72 horas.")

    def _recargo(self) -> float:
        return 1.1 if self._requiere_deposito else 1.0  # seguro +10 %

    def describir(self) -> str:
        dep = "con depósito" if self._requiere_deposito else "sin depósito"
        return (f"Equipo '{self.nombre}' ({self._tipo_equipo}, {dep}) - "
                f"${self.tarifa_hora:,.0f}/h")


class AsesoriaEspecializada(Servicio):
    tipo = "Asesoría"
    NIVELES = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre=None, tarifa_hora=None, especialidad=None,
                 nivel="junior"):
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ServicioInvalidoError("Debe indicar la especialidad.")
        nivel = nivel.strip().lower() if isinstance(nivel, str) else nivel
        if nivel not in self.NIVELES:
            raise ServicioInvalidoError(
                f"Nivel inválido {nivel!r}. Use: {', '.join(self.NIVELES)}")
        super().__init__(nombre, tarifa_hora)
        self._especialidad = especialidad.strip()
        self._nivel = nivel

    def validar_parametros(self, horas) -> None:
        if not isinstance(horas, (int, float)) or not 0.5 <= horas <= 6:
            raise ServicioInvalidoError(
                "Una asesoría dura de 0.5 a 6 horas.")

    def _recargo(self) -> float:
        return self.NIVELES[self._nivel]

    def describir(self) -> str:
        return (f"Asesoría '{self.nombre}' en {self._especialidad} "
                f"(nivel {self._nivel}) - ${self.tarifa_hora:,.0f}/h")


# ============================================================================
# SECCIÓN 5: RESERVA Y GESTOR DEL SISTEMA
# Responsable: [Integrante 4]
# try/except, try/except/else, try/except/finally y encadenamiento.
# ============================================================================
class EstadoReserva(Enum):
    PENDIENTE = "Pendiente"
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"
    FALLIDA = "Fallida"


class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado."""

    _familia = "reserva"

    def __init__(self, cliente, servicio, horas) -> None:
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un Servicio válido.")
        if isinstance(horas, bool) or not isinstance(horas, (int, float)) \
                or horas <= 0:
            raise ReservaInvalidaError(f"Duración inválida: {horas!r}")
        super().__init__()
        self.cliente = cliente
        self.servicio = servicio
        self.horas = horas
        self._estado = EstadoReserva.PENDIENTE
        self._costo = None
        self.motivo_fallo = ""

    @property
    def estado(self) -> EstadoReserva:
        return self._estado

    @property
    def costo(self):
        return self._costo

    def confirmar(self, impuesto: float = IVA, descuento: float = 0.0) -> float:
        if self._estado is not EstadoReserva.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva {self._estado.value.lower()}.")
        if not self.servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.servicio.nombre}' no está disponible.")
        self._costo = self.servicio.calcular_costo(
            self.horas, impuesto, descuento)
        self._estado = EstadoReserva.CONFIRMADA
        return self._costo

    def cancelar(self) -> None:
        if self._estado is EstadoReserva.CANCELADA:
            raise OperacionNoPermitidaError("La reserva ya está cancelada.")
        self._estado = EstadoReserva.CANCELADA
        log.info("Reserva #%s cancelada.", self.id)

    def procesar(self, impuesto: float = IVA, descuento: float = 0.0) -> bool:
        """Confirma la reserva controlando todos los errores.
        Devuelve True si se confirmó, False si falló (sin detener el programa)."""
        try:
            costo = self.confirmar(impuesto, descuento)
        except (ServicioInvalidoError, CalculoInconsistenteError) as error:
            self._estado = EstadoReserva.FALLIDA
            try:    # Encadenamiento: error de dominio + causa original
                raise ReservaInvalidaError(
                    f"Reserva #{self.id} no pudo calcularse: {error}") from error
            except ReservaInvalidaError as encadenado:
                self.motivo_fallo = str(encadenado)
                log.error("%s | causa: %r", encadenado, encadenado.__cause__)
            return False
        except SoftwareFJError as error:
            self._estado = EstadoReserva.FALLIDA
            self.motivo_fallo = str(error)
            log.error("Reserva #%s fallida: %s", self.id, error)
            return False
        else:       # solo si NO hubo excepción
            log.info("Reserva #%s confirmada. Costo: $%s", self.id, f"{costo:,.2f}")
            return True
        finally:    # siempre se ejecuta
            log.info("Fin de procesamiento de reserva #%s (estado: %s)",
                     self.id, self._estado.value)

    def describir(self) -> str:
        costo = f"${self._costo:,.2f}" if self._costo else "sin calcular"
        extra = f" | Motivo: {self.motivo_fallo}" if self.motivo_fallo else ""
        return (f"Reserva #{self.id} | {self.cliente.nombre} | "
                f"{self.servicio.nombre} | {self.horas} h | "
                f"{self._estado.value} | {costo}{extra}")


class GestorSistema:
    """Guarda clientes, servicios y reservas en listas (sin base de datos).
    Cada método registra en el log y relanza el error para que quien lo
    llame (consola o interfaz) decida cómo mostrarlo."""

    def __init__(self) -> None:
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def agregar_cliente(self, **datos) -> Cliente:
        try:
            cliente = Cliente(**datos)
        except SoftwareFJError as error:
            log.error("Registro de cliente fallido: %s", error)
            raise
        except TypeError as error:
            log.error("Parámetros incorrectos al crear cliente: %s", error)
            raise ParametroInvalidoError(str(error)) from error
        else:
            self.clientes.append(cliente)
            log.info("Cliente registrado: %s", cliente.describir())
            return cliente

    def agregar_servicio(self, clase, **datos) -> Servicio:
        try:
            servicio = clase(**datos)
        except SoftwareFJError as error:
            log.error("Creación de servicio fallida (%s): %s",
                      clase.__name__, error)
            raise
        except TypeError as error:
            log.error("Parámetros incorrectos para %s: %s", clase.__name__, error)
            raise ParametroInvalidoError(str(error)) from error
        else:
            self.servicios.append(servicio)
            log.info("Servicio creado: %s", servicio.describir())
            return servicio

    def crear_reserva(self, cliente, servicio, horas) -> Reserva:
        try:
            reserva = Reserva(cliente, servicio, horas)
        except SoftwareFJError as error:
            log.error("Reserva inválida: %s", error)
            raise
        self.reservas.append(reserva)
        log.info("Reserva #%s creada (pendiente).", reserva.id)
        return reserva


# ============================================================================
# SECCIÓN 6: SIMULACIÓN DE OPERACIONES (válidas e inválidas)
# Responsable: [Integrante 5]
# Demuestra que el programa continúa funcionando ante errores graves.
# ============================================================================
def simular(gestor: GestorSistema, salida=print) -> int:
    """Ejecuta la simulación y devuelve el número de operaciones."""
    log.info("===== INICIO DE LA SIMULACIÓN =====")
    ctx = {}
    contador = {"n": 0}

    def paso(titulo, accion):
        contador["n"] += 1
        salida(f"\n[{contador['n']:02d}] {titulo}")
        try:
            resultado = accion()
        except SoftwareFJError as error:
            salida(f"     ERROR controlado -> {type(error).__name__}: {error}")
        except Exception as error:                       # último recurso
            log.exception("Error inesperado en la simulación: %s", error)
            salida(f"     ERROR inesperado (controlado) -> {error}")
        else:
            if isinstance(resultado, Reserva) and \
                    resultado.estado is EstadoReserva.FALLIDA:
                salida(f"     ERROR controlado -> {resultado.motivo_fallo}")
            else:
                salida(f"     OK -> {resultado}")
            return resultado

    def reservar(cliente, servicio, horas, **opciones):
        reserva = gestor.crear_reserva(cliente, servicio, horas)
        reserva.procesar(**opciones)
        return reserva

    ctx["ana"] = paso("Cliente válido", lambda: gestor.agregar_cliente(
        nombre="Ana Pérez", email="ana@correo.com",
        telefono="3001234567", documento="1012345678"))
    paso("Cliente inválido (correo mal formado)", lambda: gestor.agregar_cliente(
        nombre="Luis Gómez", email="luis#correo",
        telefono="3109876543", documento="79876543"))
    paso("Cliente inválido (parámetros faltantes)",
         lambda: gestor.agregar_cliente(nombre="Carlos Ruiz",
                                        email="carlos@correo.com"))
    ctx["mario"] = paso("Cliente válido", lambda: gestor.agregar_cliente(
        nombre="Mario Díaz", email="mario@correo.com",
        telefono="3205551234", documento="52123456"))
    ctx["sala"] = paso("Servicio válido: sala de reuniones",
                       lambda: gestor.agregar_servicio(
                           ReservaSala, nombre="Sala Ejecutiva",
                           tarifa_hora=50000, capacidad=25))
    paso("Servicio inválido: equipo con tarifa negativa",
         lambda: gestor.agregar_servicio(
             AlquilerEquipo, nombre="Portátil", tarifa_hora=-10,
             tipo_equipo="Laptop"))
    ctx["equipo"] = paso("Servicio válido: alquiler de equipo",
                         lambda: gestor.agregar_servicio(
                             AlquilerEquipo, nombre="Video Beam",
                             tarifa_hora=20000, tipo_equipo="Proyector",
                             requiere_deposito=True))
    ctx["asesoria"] = paso("Servicio válido: asesoría especializada",
                           lambda: gestor.agregar_servicio(
                               AsesoriaEspecializada, nombre="Asesoría Cloud",
                               tarifa_hora=90000,
                               especialidad="Arquitectura Cloud",
                               nivel="experto"))
    paso("Servicio inválido: asesoría con nivel inexistente",
         lambda: gestor.agregar_servicio(
             AsesoriaEspecializada, nombre="Asesoría X", tarifa_hora=70000,
             especialidad="Datos", nivel="maestro"))
    paso("Reserva exitosa (sala, 3 h, con IVA)",
         lambda: reservar(ctx["ana"], ctx["sala"], 3))
    paso("Reserva fallida (12 h en una sala: duración fuera de rango)",
         lambda: reservar(ctx["ana"], ctx["sala"], 12))

    def no_disponible():
        ctx["equipo"].disponible = False
        try:
            return reservar(ctx["mario"], ctx["equipo"], 5)
        finally:                       # el servicio siempre se reactiva
            ctx["equipo"].disponible = True
    paso("Reserva fallida (servicio no disponible)", no_disponible)

    ctx["r_desc"] = paso("Reserva exitosa con descuento del 10 %",
                         lambda: reservar(ctx["mario"], ctx["asesoria"], 2,
                                          impuesto=IVA, descuento=0.10))
    paso("Cancelar una reserva confirmada", lambda: (
        ctx["r_desc"].cancelar() or ctx["r_desc"].describir()))
    paso("Cancelar de nuevo (operación no permitida)",
         lambda: ctx["r_desc"].cancelar())
    paso("Reserva con cliente inválido",
         lambda: reservar("no-soy-cliente", ctx["sala"], 2))
    paso("Reserva con cálculo inconsistente (descuento del 90 %)",
         lambda: reservar(ctx["ana"], ctx["equipo"], 4, descuento=0.9))
    paso("Sobrecarga de métodos: cotizar 2 h (base, con IVA, con IVA y 10 %)",
         lambda: [ctx["sala"].cotizar(2), ctx["sala"].cotizar(2, 0.19),
                  ctx["sala"].cotizar(2, 0.19, 0.10)])

    salida("\n--- Polimorfismo: descripción de cada servicio ---")
    for s in gestor.servicios:
        salida(" * " + s.describir())
    salida("\n--- Resumen de reservas ---")
    for r in gestor.reservas:
        salida(" * " + r.describir())
    salida(f"\nTotal de operaciones simuladas: {contador['n']}")
    salida("El programa terminó sin interrupciones. Detalle en logs/software_fj.log")
    log.info("===== FIN DE LA SIMULACIÓN (%s operaciones) =====", contador["n"])
    return contador["n"]


# ============================================================================
# SECCIÓN 7: INTERFAZ GRÁFICA (Tkinter)
# Responsable: [Integrante 5] y todo el grupo
# Pestañas: Clientes, Servicios, Reservas, Simulación y Registros (log).
# ============================================================================
_BaseTk = tk.Tk if tk else object


class App(_BaseTk):
    CAMPOS_SERVICIO = {
        "Sala": [("capacidad", "Capacidad (personas)")],
        "Equipo": [("tipo_equipo", "Tipo de equipo"),
                   ("requiere_deposito", "¿Requiere depósito? (si/no)")],
        "Asesoría": [("especialidad", "Especialidad"),
                     ("nivel", "Nivel (junior/senior/experto)")],
    }
    CLASES = {"Sala": ReservaSala, "Equipo": AlquilerEquipo,
              "Asesoría": AsesoriaEspecializada}

    def __init__(self) -> None:
        super().__init__()
        self.title("Software FJ - Clientes, Servicios y Reservas")
        self.geometry("1000x660")
        self.gestor = GestorSistema()
        self.estado = tk.StringVar(value="Listo.")
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=8, pady=8)
        self._tab_clientes()
        self._tab_servicios()
        self._tab_reservas()
        self._tab_simulacion()
        self._tab_registros()
        ttk.Label(self, textvariable=self.estado, anchor="w").pack(
            fill="x", padx=10, pady=(0, 6))
        log.info("Interfaz gráfica iniciada.")

    # ---------- utilidades ----------
    def report_callback_exception(self, exc, val, tb):
        """Último recurso: ningún error cierra la ventana."""
        log.error("Error no controlado en la interfaz: %s",
                  "".join(traceback.format_exception(exc, val, tb)))
        messagebox.showerror("Error inesperado",
                             f"{val}\n\nEl detalle quedó en el log.")

    def _ejecutar(self, accion):
        """Ejecuta una acción de la interfaz controlando todos los errores."""
        try:
            resultado = accion()
        except SoftwareFJError as error:        # ya registrado por el gestor
            self.estado.set(f"Error: {error}")
            messagebox.showerror("No se pudo completar la operación", str(error))
        except Exception as error:
            log.exception("Error inesperado: %s", error)
            self.estado.set(f"Error inesperado: {error}")
            messagebox.showerror("Error inesperado", str(error))
        else:
            self.recargar()
            return resultado

    def _tabla(self, padre, columnas, anchos):
        marco = ttk.Frame(padre)
        marco.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=9)
        for col, ancho in zip(columnas, anchos):
            tabla.heading(col, text=col)
            tabla.column(col, width=ancho, anchor="w")
        barra = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return tabla

    @staticmethod
    def _id_de(texto, nombre):
        """Extrae el id de textos como '3 - Ana Pérez'."""
        if not texto:
            raise ReservaInvalidaError(f"Seleccione un {nombre}.")
        return int(texto.split(" - ")[0])

    @staticmethod
    def _buscar(lista, ident):
        for elemento in lista:
            if elemento.id == ident:
                return elemento
        raise ReservaInvalidaError("El elemento seleccionado ya no existe.")

    @staticmethod
    def _porcentaje(texto, campo):
        return 0.0 if not str(texto).strip() else numero(texto, campo) / 100

    # ---------- pestaña Clientes ----------
    def _tab_clientes(self):
        marco = ttk.Frame(self.cuaderno)
        self.cuaderno.add(marco, text="Clientes")
        form = ttk.LabelFrame(marco, text="Registrar cliente")
        form.pack(fill="x", padx=8, pady=8)
        self.v_cli = {}
        etiquetas = [("nombre", "Nombre"), ("documento", "Documento"),
                     ("email", "Correo"), ("telefono", "Teléfono")]
        for i, (clave, texto) in enumerate(etiquetas):
            self.v_cli[clave] = tk.StringVar()
            ttk.Label(form, text=texto).grid(row=i // 2, column=(i % 2) * 2,
                                             padx=6, pady=4, sticky="e")
            ttk.Entry(form, textvariable=self.v_cli[clave], width=32).grid(
                row=i // 2, column=(i % 2) * 2 + 1, padx=6, pady=4)
        botones = ttk.Frame(form)
        botones.grid(row=2, column=0, columnspan=4, pady=6)
        ttk.Button(botones, text="Registrar cliente",
                   command=self._registrar_cliente).pack(side="left", padx=4)
        ttk.Button(botones, text="Limpiar",
                   command=self._limpiar_cliente).pack(side="left", padx=4)
        self.t_cli = self._tabla(marco, ("ID", "Nombre", "Documento",
                                         "Correo", "Teléfono"),
                                 (50, 220, 120, 250, 120))

    def _registrar_cliente(self):
        def accion():
            cliente = self.gestor.agregar_cliente(
                **{k: v.get() for k, v in self.v_cli.items()})
            self._limpiar_cliente()
            self.estado.set(f"Cliente registrado: {cliente.nombre}")
        self._ejecutar(accion)

    def _limpiar_cliente(self):
        for v in self.v_cli.values():
            v.set("")

    # ---------- pestaña Servicios ----------
    def _tab_servicios(self):
        marco = ttk.Frame(self.cuaderno)
        self.cuaderno.add(marco, text="Servicios")
        form = ttk.LabelFrame(marco, text="Crear servicio")
        form.pack(fill="x", padx=8, pady=8)
        self.v_tipo = tk.StringVar(value="Sala")
        self.v_srv_nombre = tk.StringVar()
        self.v_srv_tarifa = tk.StringVar()
        ttk.Label(form, text="Tipo").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        combo = ttk.Combobox(form, textvariable=self.v_tipo, state="readonly",
                             values=list(self.CAMPOS_SERVICIO), width=18)
        combo.grid(row=0, column=1, padx=6, pady=4)
        combo.bind("<<ComboboxSelected>>", self._campos_servicio)
        ttk.Label(form, text="Nombre").grid(row=0, column=2, padx=6, sticky="e")
        ttk.Entry(form, textvariable=self.v_srv_nombre, width=28).grid(row=0, column=3)
        ttk.Label(form, text="Tarifa por hora").grid(row=1, column=0, padx=6, sticky="e")
        ttk.Entry(form, textvariable=self.v_srv_tarifa, width=20).grid(row=1, column=1)
        self.f_extra = ttk.Frame(form)
        self.f_extra.grid(row=2, column=0, columnspan=4, pady=4)
        self.v_extra = {}
        self._campos_servicio()
        botones = ttk.Frame(form)
        botones.grid(row=3, column=0, columnspan=4, pady=6)
        ttk.Button(botones, text="Crear servicio",
                   command=self._crear_servicio).pack(side="left", padx=4)
        ttk.Button(botones, text="Activar / desactivar seleccionado",
                   command=self._alternar_disponibilidad).pack(side="left", padx=4)
        self.t_srv = self._tabla(marco, ("ID", "Tipo", "Descripción", "Disponible"),
                                 (50, 90, 650, 90))

    def _campos_servicio(self, *_):
        for hijo in self.f_extra.winfo_children():
            hijo.destroy()
        self.v_extra = {}
        for i, (clave, texto) in enumerate(self.CAMPOS_SERVICIO[self.v_tipo.get()]):
            self.v_extra[clave] = tk.StringVar()
            ttk.Label(self.f_extra, text=texto).grid(row=0, column=i * 2, padx=6)
            ttk.Entry(self.f_extra, textvariable=self.v_extra[clave],
                      width=24).grid(row=0, column=i * 2 + 1, padx=6)

    def _crear_servicio(self):
        def accion():
            tipo = self.v_tipo.get()
            datos = {"nombre": self.v_srv_nombre.get(),
                     "tarifa_hora": numero(self.v_srv_tarifa.get(), "tarifa por hora")}
            extra = {k: v.get() for k, v in self.v_extra.items()}
            if tipo == "Sala":
                extra["capacidad"] = numero(extra["capacidad"], "capacidad", True)
            elif tipo == "Equipo":
                extra["requiere_deposito"] = extra["requiere_deposito"] \
                    .strip().lower() in ("si", "sí", "s", "true", "1")
            datos.update(extra)
            servicio = self.gestor.agregar_servicio(self.CLASES[tipo], **datos)
            self.v_srv_nombre.set("")
            self.v_srv_tarifa.set("")
            self._campos_servicio()
            self.estado.set(f"Servicio creado: {servicio.nombre}")
        self._ejecutar(accion)

    def _alternar_disponibilidad(self):
        def accion():
            seleccion = self.t_srv.selection()
            if not seleccion:
                raise ServicioInvalidoError("Seleccione un servicio de la tabla.")
            ident = int(self.t_srv.item(seleccion[0])["values"][0])
            servicio = self._buscar(self.gestor.servicios, ident)
            servicio.disponible = not servicio.disponible
            estado = "disponible" if servicio.disponible else "no disponible"
            log.info("Servicio #%s marcado como %s.", servicio.id, estado)
            self.estado.set(f"'{servicio.nombre}' ahora está {estado}.")
        self._ejecutar(accion)

    # ---------- pestaña Reservas ----------
    def _tab_reservas(self):
        marco = ttk.Frame(self.cuaderno)
        self.cuaderno.add(marco, text="Reservas")
        form = ttk.LabelFrame(marco, text="Nueva reserva")
        form.pack(fill="x", padx=8, pady=8)
        self.v_r_cli = tk.StringVar()
        self.v_r_srv = tk.StringVar()
        self.v_horas = tk.StringVar()
        self.v_imp = tk.StringVar(value="19")
        self.v_desc = tk.StringVar(value="0")
        ttk.Label(form, text="Cliente").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        self.c_cli = ttk.Combobox(form, textvariable=self.v_r_cli,
                                  state="readonly", width=32)
        self.c_cli.grid(row=0, column=1, padx=6)
        ttk.Label(form, text="Servicio").grid(row=0, column=2, padx=6, sticky="e")
        self.c_srv = ttk.Combobox(form, textvariable=self.v_r_srv,
                                  state="readonly", width=40)
        self.c_srv.grid(row=0, column=3, padx=6)
        campos = [("Horas", self.v_horas, 1, 0), ("Impuesto %", self.v_imp, 1, 2),
                  ("Descuento %", self.v_desc, 2, 0)]
        for texto, var, fila, col in campos:
            ttk.Label(form, text=texto).grid(row=fila, column=col, padx=6,
                                             pady=4, sticky="e")
            ttk.Entry(form, textvariable=var, width=12).grid(
                row=fila, column=col + 1, padx=6, sticky="w")
        botones = ttk.Frame(form)
        botones.grid(row=3, column=0, columnspan=4, pady=6)
        ttk.Button(botones, text="Crear y procesar reserva",
                   command=self._crear_reserva).pack(side="left", padx=4)
        ttk.Button(botones, text="Cancelar reserva seleccionada",
                   command=self._cancelar_reserva).pack(side="left", padx=4)
        self.t_res = self._tabla(marco, ("ID", "Cliente", "Servicio", "Horas",
                                         "Estado", "Costo"),
                                 (50, 200, 220, 70, 110, 140))

    def _crear_reserva(self):
        def accion():
            cliente = self._buscar(self.gestor.clientes,
                                   self._id_de(self.v_r_cli.get(), "cliente"))
            servicio = self._buscar(self.gestor.servicios,
                                    self._id_de(self.v_r_srv.get(), "servicio"))
            horas = numero(self.v_horas.get(), "horas")
            impuesto = self._porcentaje(self.v_imp.get(), "impuesto")
            descuento = self._porcentaje(self.v_desc.get(), "descuento")
            reserva = self.gestor.crear_reserva(cliente, servicio, horas)
            if reserva.procesar(impuesto, descuento):
                messagebox.showinfo("Reserva confirmada",
                                    f"Costo total: ${reserva.costo:,.2f}")
                self.estado.set(f"Reserva #{reserva.id} confirmada.")
            else:
                messagebox.showwarning("Reserva fallida", reserva.motivo_fallo)
                self.estado.set(f"Reserva #{reserva.id} fallida.")
        self._ejecutar(accion)

    def _cancelar_reserva(self):
        def accion():
            seleccion = self.t_res.selection()
            if not seleccion:
                raise ReservaInvalidaError("Seleccione una reserva de la tabla.")
            ident = int(self.t_res.item(seleccion[0])["values"][0])
            self._buscar(self.gestor.reservas, ident).cancelar()
            self.estado.set(f"Reserva #{ident} cancelada.")
        self._ejecutar(accion)

    # ---------- pestaña Simulación ----------
    def _tab_simulacion(self):
        marco = ttk.Frame(self.cuaderno)
        self.cuaderno.add(marco, text="Simulación")
        ttk.Button(marco, text="Ejecutar simulación de operaciones "
                   "(válidas e inválidas)",
                   command=self._simular).pack(pady=8)
        self.txt_sim = tk.Text(marco, height=26, wrap="word")
        self.txt_sim.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _simular(self):
        self.txt_sim.delete("1.0", "end")

        def salida(texto):
            self.txt_sim.insert("end", texto + "\n")
            self.txt_sim.see("end")
            self.update_idletasks()
        self._ejecutar(lambda: simular(self.gestor, salida))
        self.estado.set("Simulación finalizada.")

    # ---------- pestaña Registros ----------
    def _tab_registros(self):
        marco = ttk.Frame(self.cuaderno)
        self.cuaderno.add(marco, text="Registros (log)")
        ttk.Button(marco, text="Actualizar", command=self._refrescar_log).pack(pady=8)
        self.txt_log = tk.Text(marco, height=26, wrap="none")
        self.txt_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._refrescar_log()

    def _refrescar_log(self):
        try:
            lineas = ARCHIVO_LOG.read_text(encoding="utf-8",
                                           errors="replace").splitlines()
            contenido = "\n".join(lineas[-400:])
        except OSError:
            contenido = "(Aún no hay registros.)"
        self.txt_log.delete("1.0", "end")
        self.txt_log.insert("end", contenido)
        self.txt_log.see("end")

    # ---------- refresco de tablas ----------
    def recargar(self):
        for tabla in (self.t_cli, self.t_srv, self.t_res):
            tabla.delete(*tabla.get_children())
        for c in self.gestor.clientes:
            self.t_cli.insert("", "end", values=(c.id, c.nombre, c.documento,
                                                 c.email, c.telefono))
        for s in self.gestor.servicios:
            self.t_srv.insert("", "end", values=(
                s.id, s.tipo, s.describir(), "Sí" if s.disponible else "No"))
        for r in self.gestor.reservas:
            costo = f"${r.costo:,.2f}" if r.costo else "-"
            self.t_res.insert("", "end", values=(
                r.id, r.cliente.nombre, r.servicio.nombre, r.horas,
                r.estado.value, costo))
        self.c_cli["values"] = [f"{c.id} - {c.nombre}" for c in self.gestor.clientes]
        self.c_srv["values"] = [f"{s.id} - {s.nombre}" for s in self.gestor.servicios]
        self._refrescar_log()


# ============================================================================
# SECCIÓN 8: PUNTO DE ENTRADA
# ============================================================================
def main() -> None:
    if "--consola" in sys.argv or tk is None:
        if tk is None:
            print("Tkinter no está disponible: se ejecuta el modo consola.\n")
        simular(GestorSistema())
        input("\nPresione Enter para salir...")
    else:
        App().mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:                       # la ventana nunca se cierra sin avisar
        log.exception("Error fatal al iniciar el programa")
        traceback.print_exc()
        input("\nOcurrió un error. Presione Enter para salir...")
