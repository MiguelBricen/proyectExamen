-- Migration 001: Initial Schema (Up)

-- 1. Tabla: indicadores
CREATE TABLE IF NOT EXISTS indicadores (
    id                   TEXT PRIMARY KEY,
    codigo_banco_mundial TEXT UNIQUE,
    nombre               TEXT NOT NULL,
    unidad               TEXT NOT NULL,
    descripcion          TEXT,
    created_at           TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at           TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Tabla: datos_historicos
CREATE TABLE IF NOT EXISTS datos_historicos (
    id           TEXT PRIMARY KEY,
    indicador_id TEXT NOT NULL,
    anio         INTEGER NOT NULL CHECK (anio BETWEEN 1900 AND 2100),
    valor        REAL NOT NULL CHECK (valor IS NOT NULL),
    fuente       TEXT NOT NULL DEFAULT 'Banco Mundial',
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at   TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (indicador_id) REFERENCES indicadores(id) ON DELETE CASCADE,
    UNIQUE(indicador_id, anio, fuente)
);

-- 3. Tabla: metadatos_cache_infra
CREATE TABLE IF NOT EXISTS metadatos_cache_infra (
    id              TEXT PRIMARY KEY,
    indicador_id    TEXT NOT NULL,
    anio_inicio     INTEGER NOT NULL,
    anio_fin        INTEGER NOT NULL,
    ultima_descarga TEXT NOT NULL,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (indicador_id) REFERENCES indicadores(id) ON DELETE CASCADE,
    UNIQUE(indicador_id, anio_inicio, anio_fin),
    CHECK (anio_inicio <= anio_fin)
);

-- 4. Tabla: log_cambios (Auditoría)
CREATE TABLE IF NOT EXISTS log_cambios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla            TEXT NOT NULL,
    registro_id      TEXT NOT NULL,
    tipo_operacion   TEXT NOT NULL CHECK (tipo_operacion IN ('INSERT', 'UPDATE', 'DELETE')),
    usuario          TEXT NOT NULL DEFAULT 'sistema',
    fecha            TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    datos_anteriores TEXT,
    datos_nuevos     TEXT
);

-- 5. Triggers de Auditoría para indicadores
CREATE TRIGGER IF NOT EXISTS audit_indicadores_insert AFTER INSERT ON indicadores
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_nuevos)
    VALUES (
        'indicadores',
        NEW.id,
        'INSERT',
        json_object(
            'id', NEW.id,
            'codigo_banco_mundial', NEW.codigo_banco_mundial,
            'nombre', NEW.nombre,
            'unidad', NEW.unidad
        )
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_indicadores_update AFTER UPDATE ON indicadores
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_anteriores, datos_nuevos)
    VALUES (
        'indicadores',
        NEW.id,
        'UPDATE',
        json_object(
            'id', OLD.id,
            'codigo_banco_mundial', OLD.codigo_banco_mundial,
            'nombre', OLD.nombre,
            'unidad', OLD.unidad
        ),
        json_object(
            'id', NEW.id,
            'codigo_banco_mundial', NEW.codigo_banco_mundial,
            'nombre', NEW.nombre,
            'unidad', NEW.unidad
        )
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_indicadores_delete AFTER DELETE ON indicadores
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_anteriores)
    VALUES (
        'indicadores',
        OLD.id,
        'DELETE',
        json_object(
            'id', OLD.id,
            'codigo_banco_mundial', OLD.codigo_banco_mundial,
            'nombre', OLD.nombre,
            'unidad', OLD.unidad
        )
    );
END;

-- 6. Triggers de Auditoría para datos_historicos
CREATE TRIGGER IF NOT EXISTS audit_datos_historicos_insert AFTER INSERT ON datos_historicos
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_nuevos)
    VALUES (
        'datos_historicos',
        NEW.id,
        'INSERT',
        json_object(
            'id', NEW.id,
            'indicador_id', NEW.indicador_id,
            'anio', NEW.anio,
            'valor', NEW.valor,
            'fuente', NEW.fuente
        )
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_datos_historicos_update AFTER UPDATE ON datos_historicos
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_anteriores, datos_nuevos)
    VALUES (
        'datos_historicos',
        NEW.id,
        'UPDATE',
        json_object(
            'id', OLD.id,
            'indicador_id', OLD.indicador_id,
            'anio', OLD.anio,
            'valor', OLD.valor,
            'fuente', OLD.fuente
        ),
        json_object(
            'id', NEW.id,
            'indicador_id', NEW.indicador_id,
            'anio', NEW.anio,
            'valor', NEW.valor,
            'fuente', NEW.fuente
        )
    );
END;

CREATE TRIGGER IF NOT EXISTS audit_datos_historicos_delete AFTER DELETE ON datos_historicos
BEGIN
    INSERT INTO log_cambios (tabla, registro_id, tipo_operacion, datos_anteriores)
    VALUES (
        'datos_historicos',
        OLD.id,
        'DELETE',
        json_object(
            'id', OLD.id,
            'indicador_id', OLD.indicador_id,
            'anio', OLD.anio,
            'valor', OLD.valor,
            'fuente', OLD.fuente
        )
    );
END;
