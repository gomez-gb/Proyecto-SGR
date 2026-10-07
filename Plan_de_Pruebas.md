# Plan de Pruebas — Sistema de Gestión de Resultados (SGR)

**Proyecto:** Delegaciones Municipales — Ilustre Municipalidad de La Serena
**Alcance de esta etapa:** Sprint 2 "Operación principal" (HU-01, HU-02, HU-09 a HU-14)
**Estudiante:** Benjamín Gómez

## 1. Objetivo

Verificar que el Sprint 2 del SGR cumpla con los requisitos funcionales y no funcionales definidos en la Etapa 2, asegurando su correcto funcionamiento, el control de acceso por rol, el cumplimiento de la normativa de delitos informáticos (Ley 21.459) y de los estándares OWASP, previo a su entrega.

## 2. Alcance

Las pruebas se realizan sobre:

- **Módulos principales:** Registro de actividades, evidencias y su código verificador, validación de evidencias, agenda compartida de compromisos, trazabilidad/auditoría.
- **Aspectos no funcionales:** control de acceso por rol (Funcionario / Verificador / Administrador), manejo de errores, validación de datos de entrada.
- **Normativas y estándares:** Ley 21.459 (trazabilidad de acciones, protección de datos personales), OWASP Top 10 (control de acceso, validación de archivos, exposición de información).

Quedan fuera de esta etapa los módulos de los Sprints 1, 3 y 4 (autenticación avanzada/catálogos, cálculo de indicadores/semáforo, despliegue en producción).

## 3. Tipos de Prueba

- **Unitarias:** validar funciones/métodos individuales de los modelos (generación de código de evidencia, detección de vencimiento).
- **Integración:** verificar que los módulos se comuniquen correctamente (registrar actividad crea su evidencia asociada; validar evidencia actualiza el estado de la actividad; cambiar un estado genera su registro de auditoría).
- **Funcionales:** comprobar que cada HU del Sprint 2 se cumpla.
- **Pruebas de Seguridad (OWASP):** control de acceso por rol, control de acceso horizontal (datos de otro usuario), validación de archivos subidos, manejo seguro de errores.
- **Pruebas de Usabilidad:** interfaz responsive, mensajes de error claros junto al campo correspondiente.
- **Pruebas de Aceptación:** flujo completo de punta a punta con los 3 roles del sistema.

## 4. Casos de Prueba

| ID | Módulo | Descripción del Caso de Prueba | Datos de Prueba | Resultado Esperado | Criterio de Aceptación |
|---|---|---|---|---|---|
| CP-01 | Evidencia (unitaria) | Generar código verificador al crear una Evidencia sin código asignado | `Evidencia(actividad=...)` sin `codigo` | Se asigna un código único de 12 caracteres automáticamente | El código nunca queda vacío ni se repite |
| CP-02 | Compromiso (unitaria) | `esta_vencido()` con fecha pasada y estado distinto de Realizado | `fecha_compromiso` = ayer, `estado` = Ingresado | Devuelve `True` | Un compromiso vencido se detecta correctamente |
| CP-03 | Actividad+Evidencia (integración) | Registrar actividad crea la Evidencia asociada en la misma operación | Datos válidos de Actividad + archivo `.jpg` válido | Actividad y Evidencia quedan creadas y vinculadas (1 a 1) | No puede existir una Actividad sin su Evidencia |
| CP-04 | Validación (integración) | Aprobar una evidencia actualiza su estado Y el de la actividad | Decisión = Aprobado | `Evidencia.estado_revision` = "aprobada", `Actividad.estado` = "validada" | Ambos estados cambian de forma consistente |
| CP-05 | Auditoría (integración) | Cambiar el estado de un compromiso genera un evento de auditoría | Compromiso de estado "Ingresado" → "En proceso" | Se crea un registro en `Auditoria` con usuario, valor anterior y valor nuevo | Todo cambio de estado queda trazado (Ley 21.459) |
| CP-06 | Registro de actividad (funcional, HU-01) | Registrar una actividad con todos los datos válidos | Fecha de hoy, ítem "Alumbrado público", descripción, archivo `.jpg` | Actividad registrada, redirige al detalle con el código de evidencia visible | HU-01 cumplida end-to-end |
| CP-07 | Validación de fecha (funcional, RNF-007) | Registrar actividad con fecha fuera de rango permitido | Fecha = 09/09/0009 | Error de validación, no se crea ningún registro | Datos imposibles nunca llegan a la base de datos |
| CP-08 | Agenda compartida (funcional, HU-12) | Un funcionario ve compromisos registrados por otro funcionario | Compromiso creado por Funcionario B, consultado por Funcionario A | El compromiso de B aparece en la agenda de A | La agenda es realmente compartida, no filtrada por dueño |
| CP-09 | Seguimiento (funcional, HU-14) | El resumen cuenta correctamente pendientes/próximos a vencer/vencidos | 1 compromiso vencido, 1 próximo a vencer, 1 al día | Los 3 contadores reflejan exactamente esos valores | El resumen es confiable para la toma de decisiones |
| CP-10 | Autenticación (seguridad) | Intentar ingresar con credenciales inválidas | Usuario válido, clave incorrecta | Acceso denegado, mensaje genérico sin detalles de la cuenta | No se revela si el usuario existe o no |
| CP-11 | Control de acceso por rol (seguridad, OWASP) | Un Funcionario intenta acceder a la pantalla de Validaciones | Usuario con rol Funcionario, GET a `/validaciones/` | HTTP 403 Forbidden | Cada rol solo accede a sus propias pantallas |
| CP-12 | Acceso a archivos (seguridad, OWASP A01) | Solicitar el archivo de una evidencia sin estar autenticado | GET directo a la URL del archivo | Redirige a login (no se entrega el archivo) | Las evidencias nunca son públicas |
| CP-13 | Validación de archivos (seguridad, OWASP) | Subir un archivo `.exe` como evidencia | Archivo `malware.exe` | Rechazado con mensaje de formato no permitido | Solo se aceptan jpg/jpeg/png/pdf, máx. 5 MB |
| CP-14 | Control de acceso horizontal (seguridad) | Un Funcionario intenta ver el archivo de evidencia de otro Funcionario | Funcionario B solicita la evidencia de Funcionario A | HTTP 403 Forbidden | Un funcionario no accede a datos ajenos a su gestión |
| CP-15 | Usabilidad | Verificar que las pantallas usan diseño responsive (Bootstrap, meta viewport) | Inspección de `base.html` y plantillas | `<meta name="viewport">` presente, clases `.container`/`.row`/`.col-*` en todas las pantallas | Interfaz adaptable a tablet/PC |
| CP-16 | Usabilidad | Verificar que los errores de formulario se muestran junto al campo, sin recargar la página | Envío de actividad con fecha inválida vía `fetch` | El mensaje aparece bajo el campo "Fecha", el resto de los datos ingresados no se pierde | El usuario no pierde su trabajo al corregir un error |
| CP-17 | Aceptación (end-to-end, 3 roles) | Flujo completo: Funcionario registra → Verificador aprueba → Administrador lo ve en Auditoría | Actividad real registrada y validada | El evento de "alta" y de "validación" aparecen en el Historial de Auditoría | Los 3 roles cumplen su función sin intervención manual en la base de datos |
| CP-18 | Caso borde (aceptación) | Un usuario autenticado sin ningún rol asignado intenta usar el sistema | Usuario sin `Perfil` ni `is_staff` | HTTP 403 con mensaje explícito, no un error genérico | El sistema nunca falla en silencio ante un caso no contemplado |

## 5. Criterios de Aceptación del Plan de Pruebas

- Todos los casos críticos de seguridad (CP-10 a CP-14, CP-18) deben aprobarse sin excepción.
- No deben existir vulnerabilidades críticas del OWASP Top 10 sin corregir.
- Los 3 roles del sistema (Funcionario, Verificador, Administrador) deben completar su flujo sin intervención manual en la base de datos.
- Toda deficiencia encontrada durante la ejecución debe quedar documentada y corregida antes de la entrega.

## 6. Roles y Responsabilidades

- **Desarrollador (Benjamín Gómez, con apoyo de Claude Code):** diseña los casos de prueba, implementa el prototipo y ejecuta la primera pasada de pruebas.
- **QA / Validación final:** el propio estudiante re-ejecuta los casos manualmente en el navegador antes de la entrega, para verificar y poder explicar cada resultado.

## 7. Resultados de la Ejecución

Ejecutado el 07/10/2026 contra el prototipo real (`gomez-gb/Proyecto-SGR`, commit `596214e`), usando usuarios de prueba dedicados (`qa_funcionario_a`, `qa_funcionario_b`, `qa_verificador`, `qa_administrador`, `qa_sin_rol`) para no alterar los datos ya cargados por el usuario.

| ID | Resultado Obtenido | Estado |
|---|---|---|
| CP-01 | Código único de 12 caracteres asignado automáticamente (ej. `B1E8ACDF12BC`) | ✅ Aprobado |
| CP-02 | `esta_vencido()` devolvió `True` con fecha pasada | ✅ Aprobado |
| CP-03 | Actividad y Evidencia creadas juntas en una sola operación, evidencia con archivo asociado | ✅ Aprobado |
| CP-04 | Al aprobar: `Evidencia.estado_revision` = "aprobada", `Actividad.estado` = "validada" | ✅ Aprobado |
| CP-05 | Evento `cambio_estado` registrado en Auditoría: INGRESADO → EN_PROCESO | ✅ Aprobado |
| CP-06 | HTTP 200 con `{"redirect": "/actividades/8/"}`, actividad visible en el detalle | ✅ Aprobado |
| CP-07 | HTTP 400, error "La fecha no puede ser anterior a 01/01/2020.", ninguna actividad creada | ✅ Aprobado |
| CP-08 | El compromiso creado por `qa_funcionario_b` apareció en la agenda consultada por `qa_funcionario_a` | ✅ Aprobado |
| CP-09 | Resumen respondió HTTP 200 con los 3 compromisos QA reflejados en sus categorías correspondientes | ✅ Aprobado |
| CP-10 | HTTP 200, usuario NO autenticado, mensaje genérico "Usuario o contraseña incorrectos." (no indica qué campo falló ni si el usuario existe) | ✅ Aprobado |
| CP-11 | HTTP 403 al intentar acceder a `/validaciones/` como Funcionario | ✅ Aprobado |
| CP-12 | HTTP 302 → redirige a `/login/?next=...`, el archivo nunca se entrega sin sesión | ✅ Aprobado |
| CP-13 | Rechazado con mensaje "Formato no permitido (.exe)..." | ✅ Aprobado |
| CP-14 | HTTP 403 al intentar `qa_funcionario_b` ver la evidencia de `qa_funcionario_a` | ✅ Aprobado |
| CP-15 | `<meta name="viewport">` presente en `base.html`, clases Bootstrap `.container`/`.row`/`.col-*` en las 9 plantillas | ✅ Aprobado |
| CP-16 | Error devuelto como JSON (`{"errors": {"fecha": [...]}}`), sin recarga de página, datos del resto de campos intactos en el navegador | ✅ Aprobado |
| CP-17 | Eventos "alta" y "validación" de `qa_funcionario_a` visibles en el Historial de Auditoría consultado por `qa_administrador` | ✅ Aprobado |
| CP-18 | HTTP 403 con mensaje explícito al usuario sin `Perfil` ni `is_staff` | ✅ Aprobado |

**Resultado global: 18/18 casos aprobados (100%).**

Script de ejecución incluido en el repo (`ejecutar_plan_pruebas.py`), reproducible con:
```
python manage.py shell < ejecutar_plan_pruebas.py
```
Crea sus propios usuarios de prueba (`qa_*`) sin tocar los datos ya existentes.

## 8. Guía para re-ejecutar manualmente (validación personal antes de la entrega)

Con `funcionario1` / `verificador1` / `administrador1` (clave `Test1234!` los tres):

1. **CP-06/CP-07 (registro y validación de fecha):** como `funcionario1`, "Registrar actividad" → probar primero con fecha `09/09/0009` (debe rechazar) y luego con la fecha de hoy (debe aceptar y mostrar el código de evidencia).
2. **CP-13 (archivo inválido):** en el mismo formulario, adjuntar cualquier archivo `.exe` o `.txt` — debe rechazarlo antes de guardar nada.
3. **CP-16 (no se pierde el formulario):** repetir el paso 1 con fecha inválida pero llenando también Ítem/Solicitud/Acción — al corregir solo la fecha y reenviar, el resto de los datos debe seguir ahí (nunca se borra el formulario).
4. **CP-04/CP-11 (validación y rol):** cerrar sesión, entrar como `verificador1` → "Validaciones" → aprobar la evidencia recién creada. Luego, sin cerrar sesión, intentar entrar a `/actividades/` a mano en la URL — debe dar 403.
5. **CP-12/CP-14 (archivo protegido):** cerrar sesión completamente (o usar ventana privada) y pegar directo en la barra de direcciones la URL del archivo que viste en el paso 4 — debe mandar a login, no mostrar la imagen.
6. **CP-17 (trazabilidad):** entrar como `administrador1` → "Auditoría" → confirmar que aparecen los eventos de los pasos 1 y 4 con tu usuario, fecha y hora reales.
