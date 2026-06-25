-- Migration 001: Initial Schema (Down)

DROP TRIGGER IF EXISTS audit_datos_historicos_delete;
DROP TRIGGER IF EXISTS audit_datos_historicos_update;
DROP TRIGGER IF EXISTS audit_datos_historicos_insert;
DROP TRIGGER IF EXISTS audit_indicadores_delete;
DROP TRIGGER IF EXISTS audit_indicadores_update;
DROP TRIGGER IF EXISTS audit_indicadores_insert;

DROP TABLE IF EXISTS log_cambios;
DROP TABLE IF EXISTS metadatos_cache_infra;
DROP TABLE IF EXISTS datos_historicos;
DROP TABLE IF EXISTS indicadores;
