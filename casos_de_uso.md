# Casos de Uso Definitivos — Sistema de Recomendación VARK

---

## 1. Análisis Comparativo: Requisitos vs. Funcionalidades del Proyecto

### Matriz de Cobertura RF → F

| RF | Requisito Funcional | Funcionalidad del Proyecto | Estado |
|---|---|---|---|
| RF01 | Registro de usuarios con roles diferenciados | F-01 · Registro con rol diferenciado | ✅ Cubierto |
| RF02 | Autenticación y control de sesiones seguras | F-02 · Autenticación segura con JWT | ✅ Cubierto |
| RF03 | Aplicación de test inicial de estilos VARK | F-04 · Test VARK Dinámico generado por IA ⭐ | ✅ Cubierto (con innovación) |
| RF04 | Administración de repositorio de recursos | F-06 · Carga manual de URLs + F-08 · Validador automático | ✅ Cubierto |
| RF05 | Sugerencia y validación automatizada de recursos | F-07 · Sugerencia y validación de recursos por IA ⭐ | ✅ Cubierto (con innovación) |
| RF06 | Seguimiento de interacción y comportamiento | F-11 · Motor de Perfilado Dinámico por Clickstream | ✅ Cubierto |
| RF07 | Actualización dinámica del perfil de aprendizaje | F-11 · Perfilado Dinámico (función de decaimiento temporal) | ✅ Cubierto |
| RF08 | Recomendación adaptativa de contenidos por afinidad | F-10 · Content-Based Filtering | ✅ Cubierto |
| RF09 | Generación de justificaciones para recomendaciones | F-12 · Explicabilidad de la Recomendación | ✅ Cubierto |
| RF10 | Visualización de progreso académico mediante gráficos | F-13 · Dashboard con Gráfico de Radar VARK | ✅ Cubierto |
| RF11 | Evaluación de comprensión mediante quizzes por tema | F-09 · Sistema de Quizzes por tema | ✅ Cubierto |
| RF12 | Reportes estadísticos para seguimiento docente | F-14 · Reportes para docentes | ✅ Cubierto |
| RF13 | Gestión de pruebas y experimentación | F-16 · Módulo de experimento A/B | ✅ Cubierto |
| RF14 | Gestión de jerarquía de temas y subtemas | *Sin funcionalidad explícita* (implícita en F-09/F-10) | ⚠️ Brecha — requiere caso de uso propio |
| RF15 | Administración de banco de preguntas para quizzes | F-09 · Sistema de Quizzes (gestión de preguntas) | ✅ Cubierto |
| RF16 | Trazabilidad del historial de evolución del perfil VARK | F-13 · Línea de tiempo del dashboard | ✅ Cubierto (parcial, necesita vista dedicada) |
| RF17 | Sistema de notificaciones sobre nuevos contenidos | *Sin funcionalidad explícita* | ⚠️ Brecha — requiere caso de uso propio |
| RF18 | Retroalimentación y valoraciones de recursos por alumno | Mencionado en L-02 (logs) pero no como funcionalidad core | ⚠️ Brecha — requiere caso de uso propio |
| RF19 | Revisión y aprobación docente para sugerencias de IA | F-07 · Flujo de aprobación dentro del módulo IA | ✅ Cubierto |
| RF20 | Generación y descarga de reportes en PDF | F-15 · Exportación de reportes PDF y CSV | ✅ Cubierto |
| RF21 | Configuración de parámetros del motor de recomendación | F-17 · Panel de métricas internas + F-05 · Panel admin | ✅ Cubierto |
| RF22 | Búsqueda avanzada por estilo VARK y complejidad | *Sin funcionalidad explícita* | ⚠️ Brecha — requiere caso de uso propio |

### Resumen del Análisis

| Estado | Cantidad | RF |
|---|---|---|
| ✅ Cubierto completamente | 18 | RF01–RF13, RF15, RF16, RF19, RF20, RF21 |
| ⚠️ Brecha identificada | 4 | RF14, RF17, RF18, RF22 |

**Conclusión:** El proyecto cubre 18 de 22 requisitos funcionales. Los 4 requisitos sin funcionalidad explícita asignada (RF14, RF17, RF18, RF22) son válidos y necesarios para el sistema completo. Deben materializarse como casos de uso independientes en los ciclos de desarrollo.

---

## 2. Los 22 Casos de Uso Definitivos

Cada caso de uso corresponde directamente a un RF del `contexto.md`, garantizando trazabilidad total entre requisitos y entregables de desarrollo.

| CU | Nombre del Caso de Uso | RF | Módulo | Actores |
|---|---|---|---|---|
| **CU-01** | Registrar usuario con rol diferenciado | RF01 | Identidad y Acceso | Estudiante, Docente, Admin |
| **CU-02** | Autenticar usuario y gestionar sesión segura | RF02 | Identidad y Acceso | Todos los roles |
| **CU-03** | Aplicar test VARK dinámico generado por IA | RF03 | Identidad y Acceso | Estudiante |
| **CU-04** | Gestionar jerarquía de temas y subtemas | RF14 | Repositorio de Recursos | Admin, Docente |
| **CU-05** | Administrar banco de preguntas para quizzes | RF15 | Repositorio de Recursos | Docente, Admin |
| **CU-06** | Configurar parámetros del motor de recomendación | RF21 | Motor IA / Admin | Admin |
| **CU-07** | Evaluar comprensión mediante quizzes por tema | RF11 | Repositorio de Recursos | Estudiante |
| **CU-08** | Administrar repositorio de recursos académicos | RF04 | Repositorio de Recursos | Docente, Admin |
| **CU-09** | Sugerir recursos externos mediante IA | RF05 | Repositorio de Recursos | Sistema IA |
| **CU-10** | Revisar y aprobar sugerencias de IA (docente) | RF19 | Repositorio de Recursos | Docente, Admin |
| **CU-11** | Buscar recursos por estilo VARK y complejidad | RF22 | Repositorio de Recursos | Estudiante, Docente |
| **CU-12** | Recomendar contenidos adaptativos por afinidad VARK | RF08 | Motor de Recomendación | Sistema, Estudiante |
| **CU-13** | Generar justificaciones para recomendaciones | RF09 | Motor de Recomendación | Sistema |
| **CU-14** | Registrar valoraciones y retroalimentación de recursos | RF18 | Motor de Recomendación | Estudiante |
| **CU-15** | Rastrear interacción y comportamiento del usuario | RF06 | Motor de Recomendación | Sistema (Clickstream) |
| **CU-16** | Actualizar dinámicamente el perfil de aprendizaje | RF07 | Motor de Recomendación | Sistema (Clickstream) |
| **CU-17** | Visualizar progreso académico con gráfico radar VARK | RF10 | Análisis y Reportes | Estudiante |
| **CU-18** | Consultar historial de evolución del perfil VARK | RF16 | Análisis y Reportes | Estudiante, Docente |
| **CU-19** | Emitir reportes estadísticos para seguimiento docente | RF12 | Análisis y Reportes | Docente, Admin |
| **CU-20** | Gestionar experimento A/B de personalización | RF13 | Análisis y Reportes | Admin |
| **CU-21** | Generar y descargar reportes de desempeño en PDF/CSV | RF20 | Análisis y Reportes | Admin, Docente |
| **CU-22** | Gestionar notificaciones de nuevos contenidos recomendados | RF17 | Análisis y Reportes | Estudiante, Sistema |

---

## 3. División en 3 Ciclos de Desarrollo

La distribución sigue una lógica de dependencias técnicas: cada ciclo entrega valor funcional y habilita al siguiente.

---

### CICLO 1 — Fundamentos: Identidad, Acceso y Estructura del Contenido
> **Objetivo:** Construir el núcleo de la plataforma. Al finalizar este ciclo, los usuarios pueden registrarse, autenticarse, tomar el test VARK y existir la estructura de temas y quizzes lista para recibir contenido.

| CU | Caso de Uso | RF | Prioridad |
|---|---|---|---|
| CU-01 | Registrar usuario con rol diferenciado | RF01 | 🔴 Alta |
| CU-02 | Autenticar usuario y gestionar sesión segura | RF02 | 🔴 Alta |
| CU-03 | Aplicar test VARK dinámico generado por IA | RF03 | 🔴 Alta |
| CU-04 | Gestionar jerarquía de temas y subtemas | RF14 | 🔴 Alta |
| CU-05 | Administrar banco de preguntas para quizzes | RF15 | 🟡 Media |
| CU-06 | Configurar parámetros del motor de recomendación | RF21 | 🟡 Media |
| CU-07 | Evaluar comprensión mediante quizzes por tema | RF11 | 🟡 Media |

**Total Ciclo 1: 7 casos de uso**

**Entregable:** Plataforma funcional con registro, login, test VARK inicial (IA + fallback estático), estructura de temas (Números, Cadenas, Vectores, Matrices) y quizzes operativos.

**Dependencias habilitadas para Ciclo 2:** El vector `[V, A, R, K]` del estudiante existe y los temas están definidos — condiciones necesarias para el repositorio y el motor de recomendación.

---

### CICLO 2 — Repositorio y Motor de Recomendación
> **Objetivo:** Construir el flujo completo de contenido: desde la carga y validación de recursos hasta la entrega de recomendaciones personalizadas con justificación al estudiante.

| CU | Caso de Uso | RF | Prioridad |
|---|---|---|---|
| CU-08 | Administrar repositorio de recursos académicos | RF04 | 🔴 Alta |
| CU-09 | Sugerir recursos externos mediante IA | RF05 | 🔴 Alta |
| CU-10 | Revisar y aprobar sugerencias de IA (docente) | RF19 | 🔴 Alta |
| CU-11 | Buscar recursos por estilo VARK y complejidad | RF22 | 🟡 Media |
| CU-12 | Recomendar contenidos adaptativos por afinidad VARK | RF08 | 🔴 Alta |
| CU-13 | Generar justificaciones para recomendaciones | RF09 | 🟡 Media |
| CU-14 | Registrar valoraciones y retroalimentación de recursos | RF18 | 🟡 Media |
| CU-15 | Rastrear interacción y comportamiento del usuario | RF06 | 🔴 Alta |

**Total Ciclo 2: 8 casos de uso**

**Entregable:** El repositorio de recursos está poblado (vía docente y vía IA), el motor Content-Based Filtering recomienda URLs al estudiante según su perfil VARK, se capturan eventos de interacción (Clickstream) y el estudiante puede valorar los recursos.

**Dependencias habilitadas para Ciclo 3:** Datos de interacción disponibles para analítica y evolución del perfil dinámico.

---

### CICLO 3 — Analítica, Adaptación Dinámica y Reportes
> **Objetivo:** Activar la inteligencia adaptativa del sistema (el perfil evoluciona con el uso), proporcionar dashboards, reportes descargables y el experimento A/B para validación académica.

| CU | Caso de Uso | RF | Prioridad |
|---|---|---|---|
| CU-16 | Actualizar dinámicamente el perfil de aprendizaje | RF07 | 🔴 Alta |
| CU-17 | Visualizar progreso académico con gráfico radar VARK | RF10 | 🔴 Alta |
| CU-18 | Consultar historial de evolución del perfil VARK | RF16 | 🟡 Media |
| CU-19 | Emitir reportes estadísticos para seguimiento docente | RF12 | 🔴 Alta |
| CU-20 | Gestionar experimento A/B de personalización | RF13 | 🟡 Media |
| CU-21 | Generar y descargar reportes de desempeño en PDF/CSV | RF20 | 🟡 Media |
| CU-22 | Gestionar notificaciones de nuevos contenidos recomendados | RF17 | 🟢 Baja |

**Total Ciclo 3: 7 casos de uso**

**Entregable:** El perfil VARK se actualiza automáticamente según el comportamiento real del estudiante, el dashboard es visible, el docente accede a reportes descargables, el admin puede activar el experimento A/B y el sistema envía notificaciones de nuevos recursos.

---

## 4. Resumen Ejecutivo de los 3 Ciclos

```
CICLO 1 — Fundamentos (7 CU)
  CU-01 · Registro de usuario con roles
  CU-02 · Autenticación y sesión segura
  CU-03 · Test VARK dinámico por IA
  CU-04 · Jerarquía de temas y subtemas
  CU-05 · Banco de preguntas para quizzes
  CU-06 · Configuración del motor de recomendación
  CU-07 · Quizzes por tema
        ↓
CICLO 2 — Repositorio y Recomendación (8 CU)
  CU-08 · Administrar repositorio de recursos
  CU-09 · Sugerencia de recursos por IA
  CU-10 · Aprobación docente de sugerencias IA
  CU-11 · Búsqueda por VARK y complejidad
  CU-12 · Recomendación adaptativa Content-Based
  CU-13 · Justificaciones de recomendaciones
  CU-14 · Valoraciones y retroalimentación
  CU-15 · Seguimiento de interacción (Clickstream)
        ↓
CICLO 3 — Analítica y Adaptación Dinámica (7 CU)
  CU-16 · Actualización dinámica del perfil VARK
  CU-17 · Dashboard con radar VARK y progreso
  CU-18 · Historial de evolución del perfil
  CU-19 · Reportes estadísticos para docentes
  CU-20 · Experimento A/B de personalización
  CU-21 · Exportación PDF/CSV de reportes
  CU-22 · Notificaciones de nuevos contenidos
```

**Total: 22 casos de uso | 3 ciclos | Trazabilidad 1:1 con RF01–RF22**
