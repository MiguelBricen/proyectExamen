# Dashboard Socioeconómico de Nicaragua (Arquitectura Hexagonal)

Este proyecto implementa un dashboard interactivo en **Streamlit** para analizar indicadores clave de Nicaragua utilizando datos de la **API pública del Banco Mundial**. El sistema está diseñado siguiendo los principios de la **Arquitectura Hexagonal (Ports & Adapters)** para garantizar un desacoplamiento completo entre la lógica del negocio (Dominio) y los detalles tecnológicos (Infraestructura / UI).

---

## Estructura de Capas del Proyecto

El proyecto está estructurado de la siguiente forma:

```
├── domain/                  # Capa de Dominio (Reglas de negocio y entidades puras)
│   ├── entities.py          # Entidades (IndicadorEconomico, DatoHistorico)
│   ├── value_objects.py     # Objetos de Valor (Year, GDP, Percentage, etc.)
│   ├── exceptions.py        # Excepciones propias del negocio
│   └── repositories.py      # Puertos (Interfaces/ABCs para almacenamiento y API)
│
├── application/             # Capa de Aplicación (Casos de uso y orquestación)
│   └── services.py          # DashboardApplicationService (Orquestador principal y DI)
│
├── infrastructure/          # Capa de Infraestructura (Adaptadores concretos de salida)
│   ├── database/            # Conexión SQLite y migraciones versionadas
│   ├── repositories/        # Implementaciones de SQLite y WorldBank API
│   └── cache/               # Servicio de control de expiración de caché técnica
│
├── presentation/            # Capa de Presentación (Adaptador de entrada / Interfaz)
│   ├── ui_adapter.py        # Adaptador para formatear y mapear datos en la UI
│   └── app.py               # Dashboard en Streamlit
│
└── tests/                   # Pruebas unitarias y de integración
```

---

## Diagrama de la Arquitectura (Bonus)

El siguiente diagrama detalla cómo interactúan los componentes en la Arquitectura Hexagonal y describe el **Flujo de Ejecución Normal** y el **Flujo de Fallback (Offline)**.

```mermaid
graph TD
    classDef domain fill:#1E293B,stroke:#00B4D8,stroke-width:2px,color:#fff;
    classDef app fill:#0D1E32,stroke:#A371F7,stroke-width:2px,color:#fff;
    classDef infra fill:#161B22,stroke:#30363D,stroke-width:1px,color:#8B949E;
    classDef pres fill:#0A1520,stroke:#3FB950,stroke-width:2px,color:#fff;

    %% Nodos de Capas
    subgraph Capa_Presentacion ["Capa de Presentación (Adaptador de Entrada)"]
        UI["app.py (Streamlit UI)"]:::pres
    end

    subgraph Capa_Aplicacion ["Capa de Aplicación (Casos de Uso)"]
        AS["DashboardApplicationService"]:::app
        RES["DatosIndicadorResult (DTO)"]:::app
    end

    subgraph Capa_Dominio ["Capa de Dominio (Núcleo)"]
        EE["Entidades (Indicador, Dato)"]:::domain
        VO["Value Objects (Year, GDP, etc)"]:::domain
        EX["Excepciones (ApiCaidaError, etc)"]:::domain
        P_DB["Puerto: Indicador/Dato Repo"]:::domain
        P_API["Puerto: ExternalApiRepository"]:::domain
    end

    subgraph Capa_Infraestructura ["Capa de Infraestructura (Adaptadores de Salida)"]
        A_DB["SQLite Repositories"]:::infra
        A_API["WorldBankApiRepository"]:::infra
        CS["CacheService"]:::infra
    end

    %% Relaciones / Flujo
    UI -->|1. Solicitar Datos| AS
    AS -->|2. Instanciar VO / Validar| VO
    AS -->|3. Consultar Estado Caché| CS
    
    %% Flujo Normal (Con Conexión)
    AS -->|4a. Consultar a través de Puerto| P_API
    P_API -->|Implementado por| A_API
    A_API ===>|5a. Conexión Exitosa| WB_API["API Banco Mundial (Web)"]:::infra

    %% Flujo Fallback (Sin Conexión)
    A_API -.->|5b. API caída o sin Internet| EX_ERR["Lanza ApiCaidaError (Dominio)"]:::domain
    EX_ERR -.->|6. Captura error y activa Fallback| AS
    AS ===>|7. Consultar a través de Puerto| P_DB
    P_DB -->|Implementado por| A_DB
    A_DB ===>|8. Obtener registros offline| SQLite_DB[("Base de Datos SQLite (.db)")]:::infra

    %% Retorno de Datos
    AS -->|9. Componer Resultado| RES
    RES -->|10. Datos + Estado de Origen| UI
```

---

## Mecanismo de Fallback y Modo Offline

1. **Intento de Consulta en Red (Flujo Normal)**:
   Al solicitar un indicador, el servicio `DashboardApplicationService` intenta conectarse al puerto `ExternalApiRepository` (implementado por `WorldBankApiRepository`) para descargar los datos actualizados.
2. **Registro en Caché**:
   Si la conexión tiene éxito, los datos se validan contra los Value Objects del dominio (verificando rangos de años y validez de PIB o porcentajes) y se persisten en la base de datos SQLite a través de `SQLiteDatoHistoricoRepository`. Además, se actualizan los metadatos en `CacheService`.
3. **Activación de Fallback (Modo Offline)**:
   Si la API del Banco Mundial no responde (por caída de red, timeout o errores HTTP), el adaptador de infraestructura atrapa el error de red y eleva una excepción limpia del dominio (`ApiCaidaError`). El servicio de aplicación captura esta excepción y realiza un **fallback transparente** recuperando los datos directamente del adaptador de base de datos SQLite local.
4. **Respuesta al Usuario**:
   El servicio retorna los datos junto con un indicador `fuente_efectiva` ("API" o "Base de Datos Local (Offline)"). La UI recibe esta información y, de forma transparente, renderiza los datos mostrando un mensaje amistoso de aviso en el panel lateral si el sistema está operando en modo offline.
