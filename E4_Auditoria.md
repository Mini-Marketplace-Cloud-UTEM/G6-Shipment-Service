# Auditoría de Entrega 4 (E4): Integración Sistémica - Grupo 6

En base a la rúbrica oficial (`Rubricas_Proyecto_Cloud_Arquitectura.md`), se ha realizado una auditoría exhaustiva del repositorio del Grupo 6 (Despacho) para la **Entrega 4 (E4)**.

El objetivo de esta fase es demostrar integración real, validar contratos, manejar errores y aplicar patrones técnicos.

A continuación se detalla el estado actual de cada requerimiento de la rúbrica, qué tenemos listo y qué nos falta.

---

## Estado de Requerimientos E4

### 1. Integrar con al menos 2 grupos (Consumir/proveer servicios reales)
* **Requerimiento:** Flujo integrado (Demo/Video/Capturas).
* **Estado:** 🟡 **Parcialmente Listo / Bloqueado por terceros**
* **Detalle:** Contamos con el excelente documento `docs/Auditoria_Integraciones.md` donde evidenciamos intentos de integración con **G1, G4, G5, G7 y G8**. Sin embargo, la auditoría muestra que todos estos grupos tienen errores o no han implementado nuestra llamada correctamente.
* **Falta:** Para sacar la nota máxima en la rúbrica (Integración real con 2+ grupos y flujos completos), necesitamos **ayudar o presionar a al menos 2 grupos** para que corrijan sus bugs y podamos grabar un video/demo de un flujo exitoso completo.

### 2. Validar contratos reales
* **Requerimiento:** Comparar implementación contra contrato acordado.
* **Estado:** ✅ **Listo**
* **Detalle:** Completado exitosamente a través de `docs/Auditoria_Integraciones.md`. Allí expusimos cómo G7 exige *snake_case* incumpliendo la Regla 4, cómo G5 olvida campos obligatorios (city, customer_name) o cómo G4 ni siquiera invoca nuestro endpoint de costo de envíos.

### 3. Probar casos exitosos y fallidos
* **Requerimiento:** Pruebas de integración (Colección/reporte documentado).
* **Estado:** 🟡 **Falta Recopilar Evidencia**
* **Detalle:** Tenemos la colección de Postman de E2 (`entregables_E2/postman_collection.json`) y tests automáticos en `/tests`.
* **Falta:** Debemos crear o actualizar un archivo o colección específica de E4 que incluya capturas o ejemplos documentando los **errores 400/422/500**, timeouts o respuestas inválidas que encontramos al integrar con los otros grupos, y también los flujos exitosos.

### 4. Agregar trazabilidad
* **Requerimiento:** Usar `X-Request-Id`, `X-Correlation-Id` o logs equivalentes.
* **Estado:** ✅ **Código Listo / Falta Evidencia Visual**
* **Detalle:** A nivel de código está completado. En `app/main.py` la dependencia `verify_headers` valida la llegada de estos headers, y en la emisión de eventos (`app/main.py` y `app/worker.py`) se inyecta el `correlationId` para asegurar trazabilidad asíncrona.
* **Falta:** Tomar unas **capturas de pantalla de los logs** (por ejemplo, en Render o GCP) donde se vea claramente el flujo del `X-Correlation-Id` pasando por nuestro backend y nuestro worker.

### 5. Aplicar patrón técnico asignado
* **Requerimiento:** Evidencia de patrón técnico (Eventos, Pub/Sub, Consistencia eventual).
* **Estado:** ✅ **Listo**
* **Detalle:** G6 implementó exitosamente el patrón transaccional **Outbox** + **Pub/Sub**. Guardamos eventos en la tabla `outbox_events` de Supabase en la misma transacción (`app/main.py`) y tenemos un `worker.py` que lee esos registros asíncronamente y los publica en **Google Cloud Pub/Sub**, aplicando de forma impecable consistencia eventual.
* **Falta:** Preparar la demo técnica explicando este código al profesor.

### 6. Actualizar arquitectura
* **Requerimiento:** Diagrama actualizado que refleje dependencias reales y decisiones finales.
* **Estado:** ❌ **Faltante**
* **Detalle:** En la revisión de la carpeta `/docs` y el repositorio en general, no se encontró un diagrama actualizado de arquitectura (formato Draw.io o Mermaid) creado específicamente para E4. Los pdfs en `briefing/` pueden estar desactualizados.
* **Falta:** Crear un archivo `docs/arquitectura_E4.drawio` o incluir un diagrama Mermaid en un markdown que muestre claramente:
  1. G6 Despacho (FastAPI).
  2. Base de datos (Supabase PostgreSQL) y la tabla de Outbox.
  3. El Worker Python.
  4. Google Cloud Pub/Sub (y quiénes nos escuchan, como G8 y G7).
  5. Quién nos consume por REST síncrono (G4, G5).

---

## Resumen de Acción (To-Do List)

Para asegurar la nota máxima en E4, realizar las siguientes acciones pendientes:

- [ ] Coordinar de urgencia con **2 grupos** (ej. G5 Pedidos y G8 Notificaciones) para lograr al menos 1 flujo positivo de principio a fin y grabarlo en video (Demo E4).
- [ ] Sacar pantallazos a los logs de Render/Terminal mostrando el uso de `X-Correlation-Id`.
- [ ] Exportar una colección Postman actualizada (o documentar en un markdown) mostrando una petición exitosa y una fallida de integración.
- [ ] Crear diagrama actualizado de la Arquitectura final y guardarlo en `/docs`.
