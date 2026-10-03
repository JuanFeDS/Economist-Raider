# Feature Specification: Dashboard Principal de Indicadores Económicos

**Feature Branch**: `001-main-dashboard`
**Created**: 2026-04-12
**Status**: Draft
**Input**: Dashboard principal con indicadores económicos de Colombia

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vista de Indicadores en Tiempo Real (Priority: P1)

El usuario abre el observatorio y ve de un vistazo el estado actual de los
principales indicadores económicos de Colombia: inflación, tasa de cambio,
tasa de interés de referencia y desempleo. Cada indicador muestra su valor
más reciente, la variación respecto al período anterior y su fuente oficial.

**Why this priority**: Es el núcleo del producto. Sin esta vista el
observatorio no tiene valor mínimo viable.

**Independent Test**: Abrir la aplicación y verificar que aparecen tarjetas
con valores numéricos actuales, variación y fuente para cada indicador clave.

**Acceptance Scenarios**:

1. **Given** la app está corriendo, **When** el usuario accede a la pantalla
   principal, **Then** ve al menos 5 indicadores con valor, variación y fuente
2. **Given** los datos han sido ingestados previamente, **When** el usuario
   ve un indicador, **Then** la fecha de última actualización es visible
3. **Given** un indicador no tiene datos recientes, **When** el usuario lo ve,
   **Then** se muestra el último valor disponible con su fecha y una etiqueta
   de advertencia

---

### User Story 2 - Tendencia Histórica de un Indicador (Priority: P2)

El usuario selecciona un indicador (ej: IPC) y puede ver su evolución
histórica en una gráfica, con un rango de tiempo configurable
(últimos 3, 6, 12 meses o año a año).

**Why this priority**: El contexto histórico es fundamental para entender
si un valor actual es alto, bajo o normal para la economía colombiana.

**Independent Test**: Seleccionar cualquier indicador y ver una gráfica
con al menos dos puntos de datos históricos y un selector de rango temporal.

**Acceptance Scenarios**:

1. **Given** el usuario está en la pantalla principal, **When** hace clic en
   un indicador, **Then** se despliega una gráfica con su historial
2. **Given** hay datos de más de 6 meses, **When** el usuario cambia el rango
   temporal, **Then** la gráfica se actualiza mostrando el período seleccionado
3. **Given** el usuario selecciona un rango sin datos suficientes, **Then**
   la gráfica muestra los datos disponibles con nota informativa

---

### User Story 3 - Trazabilidad de Fuentes (Priority: P3)

El usuario puede ver, para cada indicador, la fuente oficial de donde
proviene el dato (ej: DANE, Banco de la República), con un enlace al
documento o página de origen.

**Why this priority**: La confiabilidad del observatorio depende de que
el usuario pueda verificar de dónde vienen los datos.

**Independent Test**: Hacer clic en el ícono de fuente de cualquier
indicador y verificar que aparece el nombre del organismo emisor y un
enlace al origen.

**Acceptance Scenarios**:

1. **Given** el usuario ve un indicador, **When** consulta su fuente,
   **Then** ve el nombre del organismo y la URL de origen
2. **Given** la fuente es un documento oficial (PDF/página), **When** el
   usuario sigue el enlace, **Then** accede directamente al recurso original

---

### User Story 4 - Estado de Actualización del Observatorio (Priority: P4)

El usuario puede ver cuándo fue la última vez que el sistema recopiló
datos de cada fuente y si hubo errores en la última ejecución.

**Why this priority**: Permite al usuario saber si está viendo datos
frescos o si algo falló en la recolección.

**Independent Test**: Verificar que existe una sección o indicador visual
que muestra el timestamp de la última actualización exitosa por fuente.

**Acceptance Scenarios**:

1. **Given** el sistema hizo una actualización exitosa, **When** el usuario
   revisa el estado, **Then** ve el timestamp de la última recolección
2. **Given** una fuente falló en la última ejecución, **When** el usuario
   lo revisa, **Then** ve una alerta con el error y la última fecha exitosa

---

### Edge Cases

- ¿Qué muestra el dashboard si nunca se han ingestado datos?
  → Pantalla de bienvenida con instrucciones para ejecutar la primera
  recolección de datos
- ¿Qué pasa si una fuente oficial cambia su estructura y el scraper falla?
  → El indicador afectado muestra el último valor conocido con fecha y
  etiqueta de "datos no actualizados"
- ¿Qué pasa si el valor de un indicador es extremadamente atípico?
  → Se muestra con un indicador visual de alerta pero sin bloquear la vista

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE mostrar en pantalla principal un mínimo de 5
  indicadores macroeconómicos clave de Colombia
- **FR-002**: Los indicadores DEBEN incluir: Inflación (IPC), Tasa de Cambio
  (TRM), Tasa de Interés de Referencia (Banco de la República), Tasa de
  Desempleo y PIB (crecimiento trimestral)
- **FR-003**: Cada indicador DEBE mostrar: valor actual, variación respecto
  al período anterior (absoluta y porcentual) y fecha de la medición
- **FR-004**: Cada indicador DEBE estar vinculado a su fuente oficial con
  nombre del organismo y URL de origen
- **FR-005**: El sistema DEBE mostrar una gráfica histórica al seleccionar
  un indicador, con rangos configurables de 3, 6 y 12 meses
- **FR-006**: El dashboard DEBE mostrar el timestamp de la última
  actualización exitosa por fuente de datos
- **FR-007**: El sistema DEBE indicar visualmente cuando un indicador no
  ha podido ser actualizado recientemente
- **FR-008**: El dashboard DEBE ser funcional sin conexión a internet,
  mostrando los últimos datos almacenados localmente
- **FR-009**: El sistema DEBE permitir al usuario actualizar manualmente
  los datos bajo demanda, sin esperar el ciclo automático

### Key Entities

- **Indicador**: Nombre, valor, unidad de medida, fecha de medición,
  variación, fuente, categoría (macroeconómico, monetario, laboral)
- **Fuente**: Nombre del organismo, URL base, URL del recurso específico,
  fecha de último scraping exitoso, estado (activo/error)
- **SerieHistórica**: Indicador, lista de mediciones ordenadas por fecha,
  cobertura temporal disponible
- **EjecuciónRecolección**: Fuente, timestamp inicio, timestamp fin,
  registros obtenidos, errores encontrados, estado

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El usuario puede ver el estado económico actual de Colombia
  en menos de 5 segundos desde que abre la aplicación
- **SC-002**: El 100% de los valores mostrados tienen fuente oficial
  identificable y verificable
- **SC-003**: Los datos del dashboard tienen una antigüedad máxima de 24
  horas para indicadores diarios y 1 semana para indicadores semanales
- **SC-004**: El usuario puede navegar de la vista general a la tendencia
  histórica de cualquier indicador en máximo 2 interacciones
- **SC-005**: El dashboard es legible y funcional en una pantalla de
  resolución estándar (1280×720 o superior) sin scroll horizontal
- **SC-006**: El sistema mantiene el historial de al menos 24 meses de
  datos para cada indicador

## Assumptions

- Los datos se actualizan mediante ejecución local del scheduler;
  no hay un servidor siempre encendido en fase inicial
- El usuario tiene acceso a internet cuando ejecuta las recolecciones de
  datos, pero puede consultar el dashboard sin conexión
- Las fuentes oficiales (DANE, Banco de la República) publican datos en
  formatos accesibles públicamente (HTML, CSV, JSON o PDF)
- El rango de "datos históricos" comienza desde la primera recolección
  exitosa; no se importan datos históricos retroactivamente en v1
- Un solo usuario usa la aplicación localmente; no hay gestión de roles
  ni autenticación en fase inicial
- La periodicidad de actualización por defecto: TRM diaria, IPC mensual,
  tasa de interés según reuniones del Banco de la República, desempleo
  mensual, PIB trimestral
