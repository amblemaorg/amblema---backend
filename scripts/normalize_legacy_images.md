# Corrida en producción — `normalize_legacy_images.py`

Normaliza las imágenes antiguas de `resources/images` (subidas antes de que `handler_images.py`
limitara el tamaño a 1920 px): aplica la orientación EXIF, reduce el lado mayor a 1920 px y
re-codifica (JPEG calidad 82, PNG optimizado). Así la vista previa del amblemario y los PDFs dejan de
descargar fotos de 4000+ px.

- Solo modifica archivos de imagen. **No toca Mongo**: cada archivo conserva su nombre y extensión.
- Por defecto **solo simula**. Escribe únicamente con `--apply`, y antes copia cada original a
  `--backup-dir` (obligatorio).
- Escritura atómica: un corte a mitad de corrida nunca deja una imagen a medias.
- Compatible con Python 2.7 (venv de producción). Probado con Python 2.7.18 + Pillow 6.2.2 y con
  Python 3.6.15 + Pillow 8.4.0: mismos resultados.
- No requiere reiniciar supervisor/gunicorn.

Referencia (copia local de las 324 imágenes de un amblemario completo): 252 normalizadas,
174 MB → 82 MB (el amblemario completo pasa de 183 MB a 93 MB), unos 0,27 s por imagen.

## Datos del servidor

| Elemento | Valor |
|---|---|
| Repositorio | `/home/amblema/amblema-back` |
| Python | `/home/amblema/amblema-back/venv/bin/python` (2.7) |
| Usuario del servicio | `amblema` |
| Imágenes | `/home/amblema/amblema-back/resources/images` (confirmar en el paso 1) |

## 0. Requisitos previos

1. El script debe estar desplegado en el servidor:
   ```bash
   ls /home/amblema/amblema-back/scripts/normalize_legacy_images.py
   ```
2. Elegir un horario de poco uso: el script usa un núcleo de CPU durante toda la corrida.

## 1. Entrar como el usuario del servicio y comprobar el entorno

```bash
sudo -iu amblema
cd /home/amblema/amblema-back
venv/bin/python -c "import sys, PIL; print(sys.version.split()[0], PIL.__version__)"
du -sh resources/images
df -h ~
```

- Pillow debe ser **2.7 o superior** (en Python 2.7 lo habitual es 6.x).
- Si las imágenes no están en `resources/images`, usa `--root <ruta>` en todos los comandos.

## 2. Simulación (no escribe)

```bash
mkdir -p ~/backups
nohup nice -n 10 venv/bin/python scripts/normalize_legacy_images.py \
  > ~/backups/normalize_simulacion_$(date +%Y%m%d_%H%M).log 2>&1 &
tail -f ~/backups/normalize_simulacion_*.log      # Ctrl+C solo deja de mirar, no detiene el script
```

Al final muestra:
```
Revisadas: N | normalizadas (simulado): N | omitidas: N | errores: 0
Tamaño de esas imágenes: X MB -> Y MB (ahorro Z MB)
```

- **Espacio para el respaldo:** el paso 3 necesita al menos **X MB** libres (el tamaño original de las
  imágenes que se van a normalizar). Compáralo con `df -h ~`. Si no alcanza, usa un disco externo
  para `--backup-dir` o corre por subcarpetas con `--only` (paso 3b).
- Las líneas `ERROR` corresponden a archivos corruptos o ilegibles: en `--apply` esos archivos no se
  tocan.

## 3. Aplicar

**3a. Todo de una vez:**
```bash
BK=~/backups/images_originales_$(date +%Y%m%d_%H%M)
nohup nice -n 10 venv/bin/python scripts/normalize_legacy_images.py --apply --backup-dir "$BK" \
  > "$BK.log" 2>&1 &
echo "$BK"      # anotar esta ruta: se necesita para deshacer
```

**3b. Por subcarpetas**, empezando por la de los amblemarios (cada corrida en su propio respaldo):
```bash
ls resources/images
BK=~/backups/images_originales_school_years_$(date +%Y%m%d_%H%M)
nohup nice -n 10 venv/bin/python scripts/normalize_legacy_images.py --apply --only school_years \
  --backup-dir "$BK" > "$BK.log" 2>&1 &
```

Para probar primero con pocas imágenes, añade `--limit 50`.

Si se corta a mitad (reinicio, `kill`), vuelve a lanzar el **mismo** comando con un `--backup-dir`
**nuevo**: las imágenes ya normalizadas se saltan solas. Para deshacer habrá que restaurar ambos
respaldos, primero el más reciente.

## 4. Verificar

```bash
venv/bin/python scripts/normalize_legacy_images.py --only school_years --limit 20
```
Debe salir `normalizadas (simulado): 0`. Las `omitidas` son imágenes que no se pueden reducir sin
que pesen más, o archivos cuyo formato real no coincide con su extensión; se quedan como están.

En el front: **Proyectos → C.E. Mercedes Flores de Ramírez → 2025 - 2026 → PECA → Amblemario → Vista
previa**. Las fotos deben verse con la orientación correcta y la carga debe ser notablemente más rápida.
Revisa también un par de fotos en la web pública y en el backoffice.

## 5. Deshacer (solo si hace falta)

```bash
venv/bin/python scripts/normalize_legacy_images.py --restore ~/backups/images_originales_AAAAMMDD_HHMM
```

Vuelve a poner cada original desde el respaldo (lista en `manifest.tsv`). Si una imagen se reemplazó
después de la corrida, también la sobrescribe con el original.

## 6. Cerrar

Conserva el respaldo hasta haber revisado el sitio unos días. Después se puede borrar para recuperar
el espacio:
```bash
rm -rf ~/backups/images_originales_AAAAMMDD_HHMM
exit
```
