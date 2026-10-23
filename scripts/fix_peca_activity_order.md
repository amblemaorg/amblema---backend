# Corrida en producción — `fix_peca_activity_order.py`

Sincroniza el `order` de las actividades de los PECAs del año escolar activo con el configurado en
la configuración PECA del año. Corrige los PECAs creados antes del fix, que quedaron con `order=100`
(p. ej. AmbLeMonedas aparecía 2.ª en lugar de en la posición 12).

- Solo modifica campos `order` de `peca_project`. No toca amblemario, contenido ni agenda.
- Por defecto **solo simula**. Escribe únicamente con `--apply`, y antes deja un respaldo JSON.
- Compatible con Python 2.7 (venv de producción). Probado con Python 2.7.18 + pymongo 3.12.0.
- No requiere reiniciar supervisor/gunicorn: es un cambio de datos.

## Datos del servidor

| Elemento | Valor |
|---|---|
| Repositorio | `/home/amblema/amblema-back` |
| Python | `/home/amblema/amblema-back/venv/bin/python` (2.7) |
| Usuario del servicio | `amblema` |
| Config. supervisor | `/etc/supervisor/conf.d/gunicorn.conf` (de ahí sale `DB_URL`) |

## 0. Requisitos previos

1. El script debe estar desplegado en el servidor:
   ```bash
   ls /home/amblema/amblema-back/scripts/fix_peca_activity_order.py
   ```
2. Desplegar también los cambios del backend (`peca_project_service.py` copia el `order` al crear un
   PECA) y reiniciar con `sudo supervisorctl restart gunicorn`. Si no, los proyectos nuevos volverán
   a quedar desordenados. El script se puede correr antes o después de ese despliegue.
3. Elegir un momento sin cambios en la configuración PECA del año (no reordenar ni activar
   actividades mientras corre).

## 1. Entrar como el usuario del servicio

```bash
sudo -iu amblema
cd /home/amblema/amblema-back
mkdir -p ~/backups
```

## 2. Cargar `DB_URL` desde supervisor (sin escribir la clave)

```bash
export DB_URL="$(grep -o 'DB_URL="[^"]*"' /etc/supervisor/conf.d/gunicorn.conf | cut -d'"' -f2)"
[ -n "$DB_URL" ] && echo "DB_URL cargada" || echo "ERROR: DB_URL vacía"
```

Si sale `ERROR` (el usuario `amblema` no puede leer el archivo), cárgala desde una sesión con sudo:
```bash
export DB_URL="$(sudo grep -o 'DB_URL="[^"]*"' /etc/supervisor/conf.d/gunicorn.conf | cut -d'"' -f2)"
```

## 3. Respaldo de la colección (recomendado)

```bash
mongodump --uri="$DB_URL" --collection=peca_project --out=~/backups/peca_project_$(date +%Y%m%d_%H%M)
```

Si `mongodump` no está instalado, continúa: el script guarda su propio respaldo de los valores que
cambia (paso 5) y con él se puede deshacer (paso 7).

## 4. Simulación (no escribe)

```bash
venv/bin/python scripts/fix_peca_activity_order.py | tee ~/backups/fix_order_simulacion_$(date +%Y%m%d_%H%M).log
```

Revisar la salida:
- `Año escolar activo` debe ser el correcto.
- Debe listar los PECAs con desorden, cada uno con su id entre paréntesis y los valores
  `actividad: actual -> esperado`. Se esperan **C.E. Leonardo Infante, NER 484** y
  **U.E.E. Víctor Lino Gómez** (lapso 1, 9 valores cada uno).
- Si aparecen otros PECAs, también están desordenados. Decide si corregirlos todos (paso 5a) o solo
  los dos (paso 5b).

## 5. Aplicar

**5a. Todos los PECAs desordenados del año:**
```bash
venv/bin/python scripts/fix_peca_activity_order.py --apply | tee ~/backups/fix_order_apply_$(date +%Y%m%d_%H%M).log
```

**5b. Solo los dos PECAs** (usar los ids que mostró la simulación):
```bash
venv/bin/python scripts/fix_peca_activity_order.py --apply \
  --peca <ID_LEONARDO_INFANTE> --peca <ID_VICTOR_LINO_GOMEZ> \
  | tee ~/backups/fix_order_apply_$(date +%Y%m%d_%H%M).log
```

Salida esperada al final:
```
Respaldo: /home/amblema/amblema-back/peca_order_backup_AAAAMMDD_HHMMSS.json
Valores actualizados: N de N
```
Mover el respaldo junto a los demás:
```bash
mv peca_order_backup_*.json ~/backups/
```

Si dice `Aviso: algunos valores no se actualizaron`, un PECA cambió durante la corrida. Repite
desde el paso 4.

## 6. Verificar

```bash
venv/bin/python scripts/fix_peca_activity_order.py
```
Debe terminar en `PECAs con desorden: 0 | valores a corregir: 0` (con `--peca ...` si usaste 5b).

En el backoffice, abrir **Proyectos → C.E. Leonardo Infante, NER 484 → año escolar actual → PECA →
Lapso 1**: AmbLeMonedas debe estar en la posición 12, después de
"Proyecto Ambiental: Feria Científica". Repetir con U.E.E. Víctor Lino Gómez.

## 7. Deshacer (solo si hace falta)

```bash
venv/bin/python scripts/fix_peca_activity_order.py --restore ~/backups/peca_order_backup_AAAAMMDD_HHMMSS.json
```

Restaura exactamente los valores `order` previos de los campos modificados. Si se hizo el paso 3,
también se puede restaurar la colección completa con `mongorestore` (sobrescribe cualquier cambio
posterior en `peca_project`, úsalo solo como último recurso).

## 8. Cerrar

```bash
unset DB_URL
exit
```
