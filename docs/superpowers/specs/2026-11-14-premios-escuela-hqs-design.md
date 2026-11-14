# Premios a la Escuela HQS — diseño

Fecha: 2026-11-14. Repos: `amblema---backend` y `amblema-backoffice`.

## Para qué
Determinar, por año escolar, si cada escuela gana el **Premio SLB de Calidad Educativa HQS**
(Oro, Plata o Bronce) a partir de dos índices, y mostrarlo en un reporte del backoffice
exportable a PDF y Excel.

## Reglas (dictadas por el Ing. Fidel)
1. **Índice Integral AmbLeMa** = promedio simple de 4 índices **del lapso 3**:
   IAA (Índice Ambiental AmbLeMa), PPM (palabras por minuto), M2M (multiplicaciones en
   2 minutos) y 60LM (lógica-matemática). Cada índice que pase de 100 cuenta como 100.
2. **Índice de Docentes HQS** = promedio de los % de las coevaluaciones completas de la
   escuela en ese PECA (el mismo `school_index` del reporte de coevaluación).
3. **Promedio final** = (Índice Integral + Índice de Docentes HQS) / 2.
4. **Premio:** Oro 80–100 %, Plata 60–79 %, Bronce 40–59 %.

## Decisiones (confirmadas por el Ing. Fidel el 2026-11-14)
- **D1 · Escala del IAA.** El IAA guardado es la suma de 5 indicadores de 0 a 7 (máximo 35;
  la web lo muestra como "x / 35"). Se convierte a %: `IAA % = IAA / 35 × 100`, con tope 100.
  El IAA del lapso 3 de la escuela es el promedio del `index` de sus evaluadores del lapso 3
  (`hasEvaluated=True`, `isDeleted=False`, `index` no nulo).
- **D2 · Índices académicos.** Se toman de `PecaProject.school.diagnostics.lapse3`
  (`wordsPerMinIndex`, `multiplicationsPerMinIndex`, `operationsPerMinIndex`): promedio de la
  escuela ponderado por estudiantes, ya en %. El tope de 100 se aplica a ese promedio.
- **D3 · Datos incompletos.** Si falta cualquiera de los 4 índices o no hay ninguna
  coevaluación completa, la escuela **no recibe premio** y figura como "Datos incompletos",
  indicando qué falta. No se promedia con lo disponible.
- **D4 · Huecos de los rangos.** Se compara el promedio final redondeado a 2 decimales:
  `>= 80` Oro, `>= 60` Plata, `>= 40` Bronce, `< 40` "Sin premio".
- **D5 · Cálculo al vuelo.** No se guarda nada en BD: el reporte se calcula en cada consulta.
- **D6 · Etiquetas.** El término correcto es **"60LM"** (confirmado por el Ing. Fidel). Los reportes de pines del backoffice y del front decían "L60M" y ya se corrigieron.

## Fuera de alcance
- Mostrar el premio en el PECA, en el Amblemario o en la web pública.
- Guardar históricos o "congelar" el premio otorgado.
- Cambios en la coevaluación o en los diagnósticos.

## Approaches
- **A (elegido) · Endpoint de reporte nuevo + pantalla nueva en el backoffice.** Sigue el
  patrón del reporte de coevaluación (`/statistics/coevaluationsreport`). Cálculo en un helper
  puro (fácil de probar) y un servicio que junta los datos.
- B · Agregar los premios al reporte de coevaluación existente: mezcla dos reportes y su
  contrato JSON, que ya consume el backoffice.
- C · Guardar el premio en BD con un comando: añade migraciones y datos que quedan
  desactualizados al cambiar un diagnóstico o una coevaluación. Innecesario mientras sea un reporte.
