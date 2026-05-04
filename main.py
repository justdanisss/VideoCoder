import os
import re
import sys
import json
import signal
import subprocess
import threading
from pathlib import Path

R    = "\033[91m"
G    = "\033[92m"
Y    = "\033[93m"
B    = "\033[94m"
C    = "\033[96m"
DIM  = "\033[2m"
RST  = "\033[0m"
BOLD = "\033[1m"

SUPPORTED_EXT = ('.mp4', '.mkv', '.avi', '.mov', '.webm', '.ts', '.wmv', '.m4v')

LANG_MAP = {
    'es': ['spa', 'es',  'español', 'spanish'],
    'en': ['eng', 'en',  'english', 'inglés', 'ingles'],
    'fr': ['fra', 'fre', 'fr',  'french',  'francés', 'frances'],
    'de': ['deu', 'ger', 'de',  'german',  'alemán',  'aleman'],
    'it': ['ita', 'it',  'italian', 'italiano'],
    'pt': ['por', 'pt',  'portuguese', 'portugués', 'portugues'],
    'ja': ['jpn', 'ja',  'japanese', 'japonés', 'japones'],
    'zh': ['chi', 'zho', 'zh',  'chinese', 'chino'],
    'ko': ['kor', 'ko',  'korean', 'coreano'],
    'ru': ['rus', 'ru',  'russian', 'ruso'],
    'ar': ['ara', 'ar',  'arabic', 'árabe', 'arabe'],
}
LANG_NAMES = {
    'es': {'es': 'Español', 'en': 'Spanish'},
    'en': {'es': 'Inglés', 'en': 'English'},
    'fr': {'es': 'Francés', 'en': 'French'},
    'de': {'es': 'Alemán', 'en': 'German'},
    'it': {'es': 'Italiano', 'en': 'Italian'},
    'pt': {'es': 'Portugués', 'en': 'Portuguese'},
    'ja': {'es': 'Japonés', 'en': 'Japanese'},
    'zh': {'es': 'Chino', 'en': 'Chinese'},
    'ko': {'es': 'Coreano', 'en': 'Korean'},
    'ru': {'es': 'Ruso', 'en': 'Russian'},
    'ar': {'es': 'Árabe', 'en': 'Arabic'},
}

_current_output = None
UI_LANG = 'es'

STRINGS = {
    'choose_ui_lang': {
        'es': "\nLanguage / Idioma:\n   [1] English\n   [2] Espanol",
        'en': "\nLanguage / Idioma:\n   [1] English\n   [2] Espanol",
    },
    'choose_ui_lang_prompt': {'es': "  -> Choose language [1/2]: ", 'en': "  -> Choose language [1/2]: "},
    'invalid_1_2': {'es': "  Elige una opcion valida.", 'en': "  Choose a valid option."},
    'cancelled_temp_deleted': {'es': "Cancelado. Archivo temporal eliminado.", 'en': "Cancelled. Temporary file removed."},
    'checking_dependencies': {'es': "Verificando dependencias...", 'en': "Checking dependencies..."},
    'python_required': {'es': "Python 3.10+ requerido (tienes {version})", 'en': "Python 3.10+ required (you have {version})"},
    'ffmpeg_missing': {'es': "ffmpeg/ffprobe no encontrado", 'en': "ffmpeg/ffprobe not found"},
    'ffmpeg_no_x265': {'es': "ffmpeg sin libx265, reinstalando", 'en': "ffmpeg missing libx265, reinstalling"},
    'ffmpeg_no_opus': {'es': "ffmpeg sin libopus, se usara AAC", 'en': "ffmpeg missing libopus, AAC will be used"},
    'install_with_pacman': {'es': "  Instalar {packages} con pacman? [S/n]: ", 'en': "  Install {packages} with pacman? [Y/n]: "},
    'install_failed': {'es': "Instalacion fallida. Prueba: sudo pacman -S ffmpeg", 'en': "Installation failed. Try: sudo pacman -S ffmpeg"},
    'installed_ok': {'es': "Instalado correctamente.", 'en': "Installed correctly."},
    'no_dependencies': {'es': "Sin dependencias no puedo continuar.", 'en': "I can't continue without dependencies."},
    'all_ok': {'es': "Todo en orden.", 'en': "Everything looks good."},
    'delete_originals_q': {
        'es': "\nBorrar original si el compressed sale mejor? [s/N]: ",
        'en': "\nDelete original if compressed output is better? [y/N]: ",
    },
    'smart_rename_q': {
        'es': "Renombrar archivos con limpieza inteligente? [s/N]: ",
        'en': "Smart rename output files? [y/N]: ",
    },
    'track_cleanup_q': {
        'es': "Limpiar audios y subtitulos por idioma? [S/n]: ",
        'en': "Clean audio and subtitle tracks by language? [Y/n]: ",
    },
    'simulation_active': {
        'es': "Modo simulacion activo: se analizara todo pero no se comprimira nada.",
        'en': "Simulation mode active: everything will be analyzed but nothing will be compressed.",
    },
    'encoder': {'es': "Encoder", 'en': "Encoder"},
    'input_folder': {'es': ">>> Carpeta de entrada:", 'en': ">>> Input folder:"},
    'invalid_path': {'es': "Ruta no valida.", 'en': "Invalid path."},
    'found_videos': {'es': "Encontre {count} video(s).", 'en': "Found {count} video(s)."},
    'no_videos': {'es': "No encontre videos en esa carpeta.", 'en': "I couldn't find videos in that folder."},
    'selection_mode': {'es': "Modo de seleccion:", 'en': "Selection mode:"},
    'mode_manual': {'es': "Manual      - eliges audio y subs en cada archivo", 'en': "Manual      - choose audio and subtitles for each file"},
    'mode_auto': {'es': "Automatico  - eliges idiomas y el script decide solo", 'en': "Automatic   - choose languages and the script decides"},
    'choose_mode': {'es': "  -> Modo [1/2]: ", 'en': "  -> Mode [1/2]: "},
    'auto_profile_title': {'es': "Perfil de compresion automatica:", 'en': "Automatic compression profile:"},
    'profile_medium': {'es': "Intermedia  - reducir mucho sin perder apenas calidad", 'en': "Medium      - reduce a lot with minimal quality loss"},
    'profile_high': {'es': "Alta        - punto medio entre calidad y ahorro agresivo", 'en': "High        - balance between quality and aggressive savings"},
    'profile_extreme': {'es': "Extrema     - maxima compresion automatica", 'en': "Extreme     - maximum automatic compression"},
    'profile_target': {'es': "Tamano objetivo personalizado por archivo", 'en': "Custom target size per file"},
    'choose_profile': {'es': "  -> Perfil [1/2/3/4]: ", 'en': "  -> Profile [1/2/3/4]: "},
    'available_languages': {'es': "Idiomas disponibles:", 'en': "Available languages:"},
    'choose_keep_langs': {'es': "  -> Idiomas a conservar: ", 'en': "  -> Languages to keep: "},
    'keeping_langs': {'es': "Conservando: {names}", 'en': "Keeping: {names}"},
    'out_of_range': {'es': "Indice fuera de rango.", 'en': "Index out of range."},
    'invalid_input': {'es': "Entrada invalida.", 'en': "Invalid input."},
    'track_choice': {'es': "  -> Elige ({hint}): ", 'en': "  -> Choose ({hint}): "},
    'choose_one_track': {'es': "  -> Elige una pista: ", 'en': "  -> Choose one track: "},
    'automatic_decision': {'es': "Decision automatica:", 'en': "Automatic decision:"},
    'reason': {'es': "Motivo: {reason}.", 'en': "Reason: {reason}."},
    'audio': {'es': "Audio", 'en': "Audio"},
    'subs': {'es': "Subs", 'en': "Subs"},
    'original_size': {'es': "Original: {size}", 'en': "Original: {size}"},
    'simulation_output': {'es': "Simulacion: se generaria {path}", 'en': "Simulation: would generate {path}"},
    'compressing': {'es': "Comprimiendo...", 'en': "Compressing..."},
    'discarded_bigger': {'es': "Resultado descartado: el archivo comprimido no mejora el tamano original.", 'en': "Discarded result: compressed file does not improve the original size."},
    'saved_ok': {'es': "✔  {size}  ({pct:+.1f}%  ahorro: {saved})", 'en': "✔  {size}  ({pct:+.1f}%  saved: {saved})"},
    'saved_path': {'es': "💾  {path}", 'en': "💾  {path}"},
    'deleted_original': {'es': "Original eliminado para ahorrar espacio.", 'en': "Original deleted to save space."},
    'ffmpeg_error_file': {'es': "✘  FFmpeg termino con error en '{file}'.", 'en': "✘  FFmpeg ended with an error for '{file}'."},
    'total_saved': {'es': "Total ahorrado: {size}", 'en': "Total saved: {size}"},
    'process_finished': {'es': "Proceso terminado.", 'en': "Process finished."},
    'target_size_label': {'es': "Tamano objetivo", 'en': "Target Size"},
    'smart_rename_preview': {'es': "Renombrado inteligente: {name}", 'en': "Smart rename: {name}"},
    'final_renamed': {'es': "Renombrado final: {path}", 'en': "Final rename: {path}"},
    'installing': {'es': "Instalando: {packages}", 'en': "Installing: {packages}"},
    'ffmpeg_fallback_cpu': {'es': "El encoder GPU fallo. Reintentando con CPU libx265...", 'en': "GPU encoder failed. Retrying with CPU libx265..."},
    'ffmpeg_fallback_aac': {'es': "El audio con Opus fallo. Reintentando con AAC...", 'en': "Opus audio failed. Retrying with AAC..."},
    'ffmpeg_errors': {'es': "FFmpeg devolvio estos errores:", 'en': "FFmpeg returned these errors:"},
    'track_all': {'es': "todas", 'en': "all"},
    'track_none': {'es': "ninguna", 'en': "none"},
    'track_numbers_help': {'es': "o numeros separados por coma (ej: 0,2)", 'en': "or comma-separated numbers (example: 0,2)"},
    'choose_track_prompt': {'es': "  -> Elige una pista: ", 'en': "  -> Choose one track: "},
    'choose_langs_help': {'es': "Elige uno o varios separados por coma. Ej: 0 o 0,1", 'en': "Choose one or more separated by commas. Example: 0 or 0,1"},
    'auto_audio_detected': {'es': "Audio objetivo detectado ({names}). Se eliminaran otros idiomas y todos los subtitulos.", 'en': "Target audio detected ({names}). Other languages and normal subtitles will be removed."},
    'audio_kept': {'es': "Audio conservado: {name}", 'en': "Kept audio: {name}"},
    'multiple_audio_found': {'es': "Hay varias pistas de audio en los idiomas elegidos.", 'en': "Multiple audio tracks were found in the selected languages."},
    'choose_audio_to_keep': {'es': "Elige la pista de audio a conservar:", 'en': "Choose the audio track to keep:"},
    'keep_forced_subs': {'es': "Se conservaran solo los subtitulos forzados.", 'en': "Only forced subtitles will be kept."},
    'remove_subs_due_audio': {'es': "Subtitulos eliminados porque ya existe audio en el idioma objetivo.", 'en': "Subtitles removed because target-language audio already exists."},
    'subs_kept': {'es': "Subs conservados: {names}", 'en': "Kept subtitles: {names}"},
    'no_subs_for_lang': {'es': "Sin subtitulos del idioma elegido.", 'en': "No subtitles found for the selected language."},
    'no_audio_for_langs': {'es': "'{filename}' no tiene audio en los idiomas elegidos.", 'en': "'{filename}' does not contain audio in the selected languages."},
    'manual_selection_needed': {'es': "Seleccion manual necesaria:", 'en': "Manual selection required:"},
    'audio_tracks_label': {'es': "Pistas de audio:", 'en': "Audio tracks:"},
    'subtitle_tracks_label': {'es': "Subtitulos:", 'en': "Subtitles:"},
    'crf_prompt': {'es': "CRF (18=mejor/grande -> 28=peor/pequeno) [{default}]: ", 'en': "CRF (18=better/larger -> 28=worse/smaller) [{default}]: "},
    'between_0_51': {'es': "Entre 0 y 51.", 'en': "Choose a value between 0 and 51."},
    'integer_required': {'es': "Numero entero.", 'en': "Please enter an integer."},
    'output_resolution': {'es': "Resolucion de salida", 'en': "Output resolution"},
    'choose_option': {'es': "  -> Elige opcion: ", 'en': "  -> Choose option: "},
    'resolution_original': {'es': "Original", 'en': "Original"},
    'resolution_label': {'es': "Resolucion", 'en': "Resolution"},
    'skip_recompression': {'es': "Saltando recompresion: {reason}.", 'en': "Skipping recompression: {reason}."},
    'analysis_error': {'es': "Error analizando: {error}", 'en': "Analysis error: {error}"},
    'no_video_track': {'es': "Sin pista de video. Saltando.", 'en': "No video track found. Skipping."},
    'no_audio_default': {'es': "Sin audio -> se conserva el primero.", 'en': "No audio selected -> keeping the first track."},
    'fatal_error': {'es': "Error fatal: {error}", 'en': "Fatal error: {error}"},
    'lang_selection_title': {'es': "\nLanguage / Idioma:\n   [1] English\n   [2] Espanol", 'en': "\nLanguage / Idioma:\n   [1] English\n   [2] Espanol"},
    'track_index_out': {'es': "Indice fuera de rango.", 'en': "Index out of range."},
    'track_invalid': {'es': "Entrada invalida.", 'en': "Invalid input."},
    'target_size_prompt': {'es': "Tamano objetivo por archivo en MB [{default}]: ", 'en': "Target size per file in MB [{default}]: "},
    'target_size_min': {'es': "Pon al menos 20 MB para que tenga sentido.", 'en': "Use at least 20 MB so it makes sense."},
    'target_size_number': {'es': "Numero valido, por favor.", 'en': "Please enter a valid number."},
    'without_audio': {'es': "sin audio", 'en': "no audio"},
    'without_subs': {'es': "sin subtitulos", 'en': "no subtitles"},
    'forced_tag': {'es': "forzados", 'en': "forced"},
    'forced_suffix': {'es': " forzados", 'en': " forced"},
    'copy_mode': {'es': "copiar", 'en': "copy"},
    'reencode_mode': {'es': "recodificar", 'en': "reencode"},
    'audio_unknown_channels': {'es': "canales ?", 'en': "channels ?"},
    'keep_original_resolution': {'es': "original", 'en': "original"},
    'unknown_resolution': {'es': "resolucion desconocida", 'en': "unknown resolution"},
    'unknown_codec': {'es': "codec desconocido", 'en': "unknown codec"},
    'ffprobe_timeout': {'es': "ffprobe tardo demasiado", 'en': "ffprobe took too long"},
    'ffprobe_invalid': {'es': "ffprobe devolvio respuesta invalida", 'en': "ffprobe returned an invalid response"},
    'ffmpeg_missing_runtime': {'es': "ffmpeg no encontrado", 'en': "ffmpeg not found"},
    'scale_auto_4k_1080': {'es': "fuente 4K detectada, bajando a 1080p para ahorrar mucho espacio", 'en': "4K source detected, downscaling to 1080p for major savings"},
    'scale_auto_1080_720': {'es': "fuente 1080p inflada detectada, bajando a 720p", 'en': "inflated 1080p source detected, downscaling to 720p"},
    'scale_auto_720_480': {'es': "fuente 720p muy inflada detectada, bajando a 480p", 'en': "inflated 720p source detected, downscaling to 480p"},
    'scale_keep_original': {'es': "manteniendo resolucion original", 'en': "keeping original resolution"},
    'scale_target_4k_1080': {'es': "fuente 4K ajustada a 1080p para alcanzar el tamano objetivo", 'en': "4K source adjusted to 1080p for target size"},
    'scale_target_1080_720': {'es': "fuente 1080p ajustada a 720p para alcanzar el tamano objetivo", 'en': "1080p source adjusted to 720p for target size"},
    'scale_target_720_480': {'es': "fuente 720p ajustada a 480p para alcanzar el tamano objetivo", 'en': "720p source adjusted to 480p for target size"},
    'skip_hevc_low_bitrate': {'es': "ya usa HEVC y su bitrate ({bitrate:.0f} kbps) ya es muy bajo para {height}p", 'en': "it already uses HEVC and its bitrate ({bitrate:.0f} kbps) is already very low for {height}p"},
    'skip_bitrate_too_low': {'es': "su bitrate ({bitrate:.0f} kbps) ya es demasiado bajo para recomprimir con seguridad", 'en': "its bitrate ({bitrate:.0f} kbps) is already too low to recompress safely"},
    'target_already_below': {'es': "el archivo ya pesa {size:.1f} MB, por debajo del objetivo", 'en': "the file already weighs {size:.1f} MB, below the target"},
    'target_plan_reason': {'es': "objetivo {target:.1f} MB, video ~{video} kbps, audio ~{audio} kbps", 'en': "target {target:.1f} MB, video ~{video} kbps, audio ~{audio} kbps"},
    'profile_label': {'es': "Perfil", 'en': "Profile"},
    'profile_medium_short': {'es': "Intermedia", 'en': "Medium"},
    'profile_high_short': {'es': "Alta", 'en': "High"},
    'profile_extreme_short': {'es': "Extrema", 'en': "Extreme"},
}


def t(key, **kwargs):
    template = STRINGS.get(key, {}).get(UI_LANG, key)
    return template.format(**kwargs)


def lang_name(code):
    entry = LANG_NAMES.get(code)
    if isinstance(entry, dict):
        return entry.get(UI_LANG, code)
    return entry or code


def choose_ui_language():
    global UI_LANG
    print(t('lang_selection_title'))
    while True:
        raw = input(t('choose_ui_lang_prompt')).strip()
        if raw == '1':
            UI_LANG = 'en'
            return
        if raw == '2':
            UI_LANG = 'es'
            return
        print(f"  {R}{t('invalid_1_2')}{RST}")


def ask_yes_no(prompt_key, default=False, **kwargs):
    raw = input(t(prompt_key, **kwargs)).strip().lower()
    if raw == '':
        return default
    return raw in ('s', 'si', 'sí', 'y', 'yes')

def _cleanup_handler(sig, frame):
    if _current_output and os.path.exists(_current_output):
        os.remove(_current_output)
        print(f"\n{Y}{t('cancelled_temp_deleted')}{RST}")
    sys.exit(0)

signal.signal(signal.SIGINT, _cleanup_handler)


# ── Auto-instalación ──────────────────────────
def _cmd_exists(name):
    import shutil
    return shutil.which(name) is not None

def _pacman_install(packages):
    print(f"{Y}  {t('installing', packages=' '.join(packages))}{RST}")
    return subprocess.run(['sudo', 'pacman', '-S', '--needed', '--noconfirm'] + packages).returncode == 0

def _ffmpeg_has_codec(codec):
    try:
        out = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'],
                             capture_output=True, text=True, timeout=5).stdout
        return codec in out
    except Exception:
        return False

def ensure_dependencies():
    print(f"\n{BOLD}{t('checking_dependencies')}{RST}")
    if sys.version_info < (3, 10):
        print(f"{R}{t('python_required', version=sys.version)}{RST}")
        sys.exit(1)
    missing = []
    if not _cmd_exists('ffmpeg') or not _cmd_exists('ffprobe'):
        print(f"  {Y}{t('ffmpeg_missing')}{RST}")
        missing.append('ffmpeg')
    else:
        if not _ffmpeg_has_codec('libx265'):
            print(f"  {Y}{t('ffmpeg_no_x265')}{RST}")
            missing.append('ffmpeg')
        if not _ffmpeg_has_codec('libopus'):
            print(f"  {Y}{t('ffmpeg_no_opus')}{RST}")
    if missing:
        ans = input(t('install_with_pacman', packages=', '.join(missing))).strip().lower()
        if ans in ('', 's', 'si', 'y', 'yes'):
            if not _pacman_install(missing) or not _cmd_exists('ffmpeg'):
                print(f"{R}{t('install_failed')}{RST}")
                sys.exit(1)
            print(f"  {G}{t('installed_ok')}{RST}")
        else:
            print(f"{R}{t('no_dependencies')}{RST}")
            sys.exit(0)
    else:
        print(f"  {G}{t('all_ok')}{RST}")


# ── GPU ──────────────────────────────────────
def detect_gpu_encoder():
    encs = [('hevc_nvenc','NVIDIA NVENC'),('hevc_amf','AMD AMF'),('hevc_videotoolbox','Apple VT')]
    try:
        out = subprocess.run(['ffmpeg','-hide_banner','-encoders'],
                             capture_output=True,text=True,timeout=5).stdout
        for enc, label in encs:
            if enc in out:
                return enc, label
    except Exception:
        pass
    return 'libx265', 'CPU libx265'


# ── Audio codec ───────────────────────────────
def _pick_audio_codec():
    return 'libopus' if _ffmpeg_has_codec('libopus') else 'aac'


def _build_ffmpeg_cmd(input_path, output_path, v_map, audio_tracks, subtitle_tracks, encoder, encode_plan, preferred_audio_codec=None):
    preferred_audio_codec = preferred_audio_codec or _pick_audio_codec()
    ext = Path(output_path).suffix.lower()
    # MP4 solo admite mov_text; MKV admite casi todo
    sub_codec = 'mov_text' if ext == '.mp4' else 'copy'

    cmd = ['ffmpeg', '-y', '-i', input_path]
    cmd += ['-map', f'0:{v_map}']
    for track in audio_tracks:
        cmd += ['-map', f"0:{track['index']}"]
    for track in subtitle_tracks:
        cmd += ['-map', f"0:{track['index']}"]
    cmd += ['-map_metadata', '0']
    if encode_plan.get('scale_height'):
        cmd += ['-vf', f"scale=-2:{encode_plan['scale_height']}"]

    if encode_plan['kind'] == 'target_size':
        video_bitrate_k = str(encode_plan['video_bitrate_k'])
        maxrate_k = str(int(encode_plan['video_bitrate_k'] * 1.35))
        bufsize_k = str(int(encode_plan['video_bitrate_k'] * 2))
        if encoder == 'hevc_nvenc':
            cmd += ['-c:v', 'hevc_nvenc', '-rc', 'vbr', '-b:v', f'{video_bitrate_k}k',
                    '-maxrate', f'{maxrate_k}k', '-bufsize', f'{bufsize_k}k', '-preset', 'p4']
        elif encoder == 'hevc_amf':
            cmd += ['-c:v', 'hevc_amf', '-rc', 'vbr_peak', '-b:v', f'{video_bitrate_k}k',
                    '-maxrate', f'{maxrate_k}k', '-quality', 'balanced']
        elif encoder == 'hevc_videotoolbox':
            cmd += ['-c:v', 'hevc_videotoolbox', '-b:v', f'{video_bitrate_k}k']
        else:
            cmd += ['-c:v', 'libx265', '-b:v', f'{video_bitrate_k}k', '-maxrate', f'{maxrate_k}k',
                    '-bufsize', f'{bufsize_k}k', '-preset', 'medium']
    elif encoder == 'hevc_nvenc':
        cmd += ['-c:v', 'hevc_nvenc', '-rc', 'vbr', '-cq', str(encode_plan['crf']), '-preset', 'p4']
    elif encoder == 'hevc_amf':
        cmd += ['-c:v', 'hevc_amf', '-quality', 'balanced', '-rc', 'cqp', '-qp_i', str(encode_plan['crf'])]
    elif encoder == 'hevc_videotoolbox':
        cmd += ['-c:v', 'hevc_videotoolbox', '-b:v', '2000k']
    else:
        cmd += ['-c:v', 'libx265', '-crf', str(encode_plan['crf']), '-preset', 'medium']

    for i, track in enumerate(audio_tracks):
        if track.get('copy_ok'):
            cmd += [f'-c:a:{i}', 'copy']
            continue
        audio_codec = choose_audio_encoder(track, preferred_audio_codec)
        cmd += [f'-c:a:{i}', audio_codec, f'-b:a:{i}', choose_audio_bitrate(track)]

    if subtitle_tracks:
        cmd += ['-c:s', sub_codec]

    if audio_tracks:
        cmd += ['-disposition:a:0', 'default']
        for i in range(1, len(audio_tracks)):
            cmd += [f'-disposition:a:{i}', '0']

    if subtitle_tracks:
        for i, track in enumerate(subtitle_tracks):
            disposition = 'forced' if track.get('forced') else ('default' if track.get('default') else '0')
            cmd += [f'-disposition:s:{i}', disposition]

    cmd.append(output_path)
    return cmd


def _should_fallback_to_cpu(stderr_text, encoder):
    if encoder == 'libx265':
        return False
    gpu_errors = (
        'CUDA_ERROR_NO_DEVICE',
        'no CUDA-capable device is detected',
        'Error while opening encoder',
        'Could not open encoder before EOF',
        'videotoolbox',
        'amf',
    )
    lowered = stderr_text.lower()
    return any(err.lower() in lowered for err in gpu_errors)


def _should_fallback_to_aac(stderr_text, preferred_audio_codec):
    if preferred_audio_codec != 'libopus':
        return False
    lowered = stderr_text.lower()
    audio_errors = (
        'libopus',
        'could not open encoder before eof',
        'invalid argument',
    )
    return all(token in lowered for token in audio_errors)


# ── Analisis ─────────────────────────────────
def get_video_info(file_path):
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', '-show_entries',
        'stream=index,codec_type,codec_name,width,height,bit_rate,channels,channel_layout,disposition:stream_tags=language,title',
        '-show_entries', 'format=duration,size,bit_rate', file_path
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip())
        return json.loads(r.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(t('ffprobe_timeout'))
    except json.JSONDecodeError:
        raise RuntimeError(t('ffprobe_invalid'))


# ── Progreso ──────────────────────────────────
def _parse_time(t):
    try:
        parts = t.strip().split(':')
        return sum(float(p) * 60**i for i, p in enumerate(reversed(parts)))
    except Exception:
        return 0.0

def _progress_reader(proc, duration):
    bar_width = 30
    pattern = re.compile(r'time=(\d+:\d+:\d+\.\d+)')
    for line in proc.stderr:
        m = pattern.search(line)
        if m and duration > 0:
            elapsed = _parse_time(m.group(1))
            pct = min(elapsed / duration, 1.0)
            filled = int(bar_width * pct)
            bar = '█' * filled + '░' * (bar_width - filled)
            eta_s = max(0.0, (duration - elapsed) / max(pct, 0.001) * (1 - pct))
            eta_str = f"{int(eta_s//60):02d}:{int(eta_s%60):02d}"
            print(f"\r  {C}[{bar}]{RST} {Y}{pct*100:5.1f}%{RST}  ETA {DIM}{eta_str}{RST}  ",
                  end='', flush=True)
    print()


# ── Compresion ────────────────────────────────
def compress_video(input_path, output_path, v_map, a_maps, s_maps, encoder, encode_plan, duration):
    global _current_output
    _current_output = output_path

    selected_encoder = encoder
    preferred_audio_codec = _pick_audio_codec()

    try:
        for attempt in range(3):
            cmd = _build_ffmpeg_cmd(
                input_path, output_path, v_map, a_maps, s_maps, selected_encoder, encode_plan, preferred_audio_codec
            )
            print(f"\n{DIM}CMD: {' '.join(cmd)}{RST}")

            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, text=True, bufsize=1)
            stderr_lines = []

            def _tee_progress():
                bar_width = 30
                pattern = re.compile(r'time=(\d+:\d+:\d+\.\d+)')
                for line in proc.stderr:
                    stderr_lines.append(line.rstrip())
                    m = pattern.search(line)
                    if m and duration > 0:
                        elapsed = _parse_time(m.group(1))
                        pct = min(elapsed / duration, 1.0)
                        filled = int(bar_width * pct)
                        bar = '█' * filled + '░' * (bar_width - filled)
                        eta_s = max(0.0, (duration - elapsed) / max(pct, 0.001) * (1 - pct))
                        eta_str = f"{int(eta_s//60):02d}:{int(eta_s%60):02d}"
                        print(
                            f"\r  {C}[{bar}]{RST} {Y}{pct*100:5.1f}%{RST}  ETA {DIM}{eta_str}{RST}  ",
                            end='', flush=True
                        )
                print()

            progress_thread = threading.Thread(target=_tee_progress, daemon=True)
            progress_thread.start()
            proc.wait()
            progress_thread.join()

            if proc.returncode == 0:
                return True

            if os.path.exists(output_path):
                os.remove(output_path)

            stderr_text = "\n".join(stderr_lines)
            if attempt == 0 and _should_fallback_to_cpu(stderr_text, selected_encoder):
                print(f"{Y}{t('ffmpeg_fallback_cpu')}{RST}")
                selected_encoder = 'libx265'
                continue
            if _should_fallback_to_aac(stderr_text, preferred_audio_codec):
                print(f"{Y}{t('ffmpeg_fallback_aac')}{RST}")
                preferred_audio_codec = 'aac'
                continue

            if stderr_lines:
                print(f"{R}{t('ffmpeg_errors')}{RST}")
                for line in stderr_lines[-20:]:
                    if line.strip():
                        print(f"  {line}")
            return False
    except FileNotFoundError:
        raise RuntimeError(t('ffmpeg_missing_runtime'))
    finally:
        _current_output = None


# ── Input helpers ─────────────────────────────
def _is_all(s):
    return s.lower() in ('a', 'all', 'todos')

def _is_none(s):
    return s.lower() in ('n', 'none', 'ninguno')

def pick_tracks(label, tracks, allow_none=False):
    if not tracks:
        return []
    print(f"\n  {BOLD}{label}{RST}")
    for i, track in enumerate(tracks):
        forced = t('forced_suffix') if track.get('forced') else ""
        print(f"   {C}[{i}]{RST} stream #{track['index']}  lang={Y}{track['lang']}{RST}  {DIM}{track['extra']}{forced}{RST}")
    hint = f"{C}a{RST}={t('track_all')}"
    if allow_none:
        hint += f"  {C}n{RST}={t('track_none')}"
    hint += f"  {t('track_numbers_help')}"
    while True:
        raw = input(t('track_choice', hint=hint)).strip()
        if _is_all(raw):
            return [t['index'] for t in tracks]
        if allow_none and _is_none(raw):
            return []
        try:
            chosen = [int(x.strip()) for x in raw.split(',') if x.strip()]
            if chosen and all(0 <= c < len(tracks) for c in chosen):
                return [tracks[c]['index'] for c in chosen]
            print(f"  {R}{t('track_index_out')}{RST}")
        except ValueError:
            print(f"  {R}{t('track_invalid')}{RST}")


def pick_one_track(label, tracks):
    if not tracks:
        return []
    print(f"\n  {BOLD}{label}{RST}")
    for i, track in enumerate(tracks):
        forced = t('forced_suffix') if track.get('forced') else ""
        print(f"   {C}[{i}]{RST} stream #{track['index']}  lang={Y}{track['lang']}{RST}  {DIM}{track['extra']}{forced}{RST}")
    while True:
        raw = input(t('choose_track_prompt')).strip()
        try:
            chosen = int(raw)
            if 0 <= chosen < len(tracks):
                return [tracks[chosen]['index']]
            print(f"  {R}{t('track_index_out')}{RST}")
        except ValueError:
            print(f"  {R}{t('track_invalid')}{RST}")


# ── Modo automatico ───────────────────────────
def _normalize_lang(tag):
    tag = tag.lower().strip()
    for code, aliases in LANG_MAP.items():
        if tag in aliases:
            return code
    return 'und'

def choose_target_langs():
    print(f"\n  {BOLD}{t('available_languages')}{RST}")
    codes = list(LANG_MAP.keys())
    for i, code in enumerate(codes):
        print(f"   {C}[{i}]{RST} {lang_name(code)}")
    print(f"\n  {t('choose_langs_help')}")
    while True:
        raw = input(t('choose_keep_langs')).strip()
        try:
            chosen = [int(x.strip()) for x in raw.split(',') if x.strip()]
            if chosen and all(0 <= c < len(codes) for c in chosen):
                selected = [codes[c] for c in chosen]
                names = ', '.join(lang_name(c) for c in selected)
                print(f"  {G}{t('keeping_langs', names=names)}{RST}")
                return selected
            print(f"  {R}{t('out_of_range')}{RST}")
        except ValueError:
            print(f"  {R}{t('invalid_input')}{RST}")

def auto_select_tracks(audios, subs, target_langs, filename):
    def matches(lang_tag):
        return _normalize_lang(lang_tag) in target_langs

    matched_audio_tracks = [track for track in audios if matches(track['lang'])]

    if matched_audio_tracks:
        target_names = ', '.join(lang_name(code) for code in target_langs)
        print(f"  {G}{t('auto_audio_detected', names=target_names)}{RST}")
        if len(matched_audio_tracks) == 1:
            selected_a = [matched_audio_tracks[0]['index']]
            kept_name = lang_name(_normalize_lang(matched_audio_tracks[0]['lang']))
            print(f"  {G}{t('audio_kept', name=kept_name)}{RST}")
        else:
            print(f"  {Y}{t('multiple_audio_found')}{RST}")
            selected_a = pick_one_track(t('choose_audio_to_keep'), matched_audio_tracks)
        forced_subs = [track['index'] for track in subs if track.get('forced')]
        if forced_subs:
            print(f"  {DIM}{t('keep_forced_subs')}{RST}")
        else:
            print(f"  {DIM}{t('remove_subs_due_audio')}{RST}")
        return selected_a, forced_subs

    matched_audio = [track['index'] for track in audios if matches(track['lang'])]
    matched_subs  = [track['index'] for track in subs if matches(track['lang']) or track.get('forced')]

    if matched_audio:
        a_names = ', '.join(
            lang_name(_normalize_lang(track['lang']))
            for track in audios if matches(track['lang'])
        )
        print(f"  {G}{t('audio_kept', name=a_names)}{RST}")
        if matched_subs:
            s_names = ', '.join(
                lang_name(_normalize_lang(track['lang']))
                for track in subs if track['index'] in matched_subs
            )
            print(f"  {G}{t('subs_kept', names=s_names)}{RST}")
        else:
            print(f"  {DIM}{t('no_subs_for_lang')}{RST}")
        return matched_audio, matched_subs
    else:
        # No hay audio en el idioma objetivo → seleccion manual
        print(f"\n  {Y}{t('no_audio_for_langs', filename=filename)}{RST}")
        print(f"  {Y}{t('manual_selection_needed')}{RST}")
        selected_a = pick_tracks(t('audio_tracks_label'), audios)
        selected_s = pick_tracks(t('subtitle_tracks_label'), subs, allow_none=True)
        return selected_a, selected_s


# ── Utilidades ────────────────────────────────
def ask_crf(default=24):
    while True:
        raw = input(f"\n  {BOLD}{t('crf_prompt', default=default)}{RST}").strip()
        if raw == '':
            return default
        try:
            v = int(raw)
            if 0 <= v <= 51:
                return v
            print(f"  {R}{t('between_0_51')}{RST}")
        except ValueError:
            print(f"  {R}{t('integer_required')}{RST}")


def ask_target_size_mb(default=120):
    while True:
        raw = input(f"\n  {BOLD}{t('target_size_prompt', default=default)}{RST}").strip()
        if raw == '':
            return default
        try:
            value = float(raw.replace(',', '.'))
            if value >= 20:
                return value
            print(f"  {R}{t('target_size_min')}{RST}")
        except ValueError:
            print(f"  {R}{t('target_size_number')}{RST}")


def choose_auto_profile():
    print(f"\n  {BOLD}{t('auto_profile_title')}{RST}")
    print(f"   {C}[1]{RST} {t('profile_medium')}")
    print(f"   {C}[2]{RST} {t('profile_high')}")
    print(f"   {C}[3]{RST} {t('profile_extreme')}")
    print(f"   {C}[4]{RST} {t('profile_target')}")
    mapping = {'1': 'medium', '2': 'high', '3': 'extreme', '4': 'target'}
    while True:
        raw = input(t('choose_profile')).strip()
        if raw in mapping:
            return mapping[raw]
        print(f"  {R}{t('invalid_1_2')}{RST}")


def auto_profile_label(profile):
    labels = {
        'medium': t('profile_medium_short'),
        'high': t('profile_high_short'),
        'extreme': t('profile_extreme_short'),
        'target': t('target_size_label'),
    }
    return labels.get(profile, profile)


def ask_resolution_target(source_height):
    options = [('0', t('resolution_original'), 0)]
    if source_height >= 2160:
        options.append(('1', '1080p', 1080))
    if source_height >= 1080:
        options.append(('2', '720p', 720))
    if source_height >= 720:
        options.append(('3', '480p', 480))

    print(f"\n  {BOLD}{t('output_resolution')}{RST}")
    for key, label, _ in options:
        print(f"   {C}[{key}]{RST} {label}")

    valid = {key: value for key, _, value in options}
    while True:
        raw = input(t('choose_option')).strip()
        if raw in valid:
            return valid[raw]
        print(f"  {R}{t('invalid_1_2')}{RST}")


def _safe_int(value, default=0):
    try:
        if value in (None, '', 'N/A'):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _pick_default_track(tracks, selected_indexes):
    order = {track['index']: track for track in tracks}
    selected = [order[idx] for idx in selected_indexes if idx in order]
    if not selected:
        return []
    default_tracks = [track for track in selected if track.get('default')]
    return default_tracks[0] if default_tracks else selected[0]


def should_copy_audio(track):
    codec = (track.get('codec') or '').lower()
    bitrate = _safe_int(track.get('bit_rate'))
    channels = _safe_int(track.get('channels'))
    if codec not in ('aac', 'opus', 'libopus'):
        return False
    if channels >= 6:
        return bitrate > 0 and bitrate <= 192000
    if channels >= 2:
        return bitrate > 0 and bitrate <= 160000
    return bitrate > 0 and bitrate <= 128000


def choose_audio_encoder(track, preferred_codec=None):
    codec = preferred_codec or _pick_audio_codec()
    channels = _safe_int(track.get('channels'))
    layout = (track.get('channel_layout') or '').lower()
    if codec == 'libopus':
        if channels > 6:
            return 'aac'
        if any(tag in layout for tag in ('7.1', 'hexadecagonal', '22.2')):
            return 'aac'
    return codec


def choose_audio_bitrate(track):
    channels = _safe_int(track.get('channels'))
    if channels >= 8:
        return '192k'
    if channels >= 6:
        return '144k'
    if channels >= 2:
        return '96k'
    return '64k'


def estimate_audio_bitrate_kbps(audio_tracks):
    total = 0
    for track in audio_tracks:
        if track.get('copy_ok'):
            bitrate = _safe_int(track.get('bit_rate')) // 1000
            total += bitrate if bitrate > 0 else 128
        else:
            total += int(choose_audio_bitrate(track).rstrip('k'))
    return total


def summarize_audio_plan(audio_tracks):
    if not audio_tracks:
        return t('without_audio')
    parts = []
    for track in audio_tracks:
        mode = t('copy_mode') if track.get('copy_ok') else t('reencode_mode')
        channels = _safe_int(track.get('channels'))
        channel_label = f"{channels}ch" if channels > 0 else t('audio_unknown_channels')
        target = ''
        if not track.get('copy_ok'):
            target_codec = choose_audio_encoder(track)
            target = f" -> {target_codec} {choose_audio_bitrate(track)}"
        parts.append(f"#{track['index']} {track['codec']} {track['lang']} {channel_label} [{mode}{target}]")
    return ', '.join(parts)


def summarize_subtitle_plan(subtitle_tracks):
    if not subtitle_tracks:
        return t('without_subs')
    parts = []
    for track in subtitle_tracks:
        label = f"#{track['index']} {track['lang']}"
        if track.get('forced'):
            label += f" {t('forced_tag')}"
        parts.append(label)
    return ', '.join(parts)


def choose_auto_scale(video_stream, format_info, crf, profile='extreme'):
    height = _safe_int(video_stream.get('height'))
    width = _safe_int(video_stream.get('width'))
    bitrate = _safe_int(video_stream.get('bit_rate')) or _safe_int(format_info.get('bit_rate'))
    bitrate_kbps = bitrate / 1000 if bitrate else 0
    duration = max(float(format_info.get('duration', 0) or 0), 1.0)
    size_mb = _safe_int(format_info.get('size')) / (1024 * 1024)
    size_per_min_mb = size_mb / max(duration / 60.0, 1.0)
    is_hd_plus = height >= 900 or width >= 1600
    is_above_2k = width > 2048 or height > 1200

    if profile == 'medium':
        if is_above_2k:
            return 1080, t('scale_auto_4k_1080')
        return 0, t('scale_keep_original')

    if height >= 2160:
        return 1080, t('scale_auto_4k_1080')
    if is_hd_plus and (bitrate_kbps >= 4500 or size_per_min_mb >= 18 or crf >= (25 if profile == 'high' else 26)):
        return 720, t('scale_auto_1080_720')
    if profile == 'high':
        return 0, t('scale_keep_original')
    if 720 <= height < 900 and (bitrate_kbps >= 5000 or size_per_min_mb >= 28) and crf >= 28:
        return 480, t('scale_auto_720_480')
    return 0, t('scale_keep_original')


def choose_target_scale(video_stream, target_size_mb, target_total_kbps):
    height = _safe_int(video_stream.get('height'))
    width = _safe_int(video_stream.get('width'))
    is_hd_plus = height >= 900 or width >= 1600
    if height >= 2160:
        return 1080, t('scale_target_4k_1080')
    if is_hd_plus and (target_size_mb <= 180 or target_total_kbps <= 2200):
        return 720, t('scale_target_1080_720')
    if 720 <= height < 900 and (target_size_mb <= 55 or target_total_kbps <= 700):
        return 480, t('scale_target_720_480')
    return 0, t('scale_keep_original')


def summarize_scale(scale_height):
    if not scale_height:
        return t('keep_original_resolution')
    return f"{scale_height}p"


def choose_auto_crf(video_stream, format_info, profile='extreme'):
    codec = (video_stream.get('codec_name') or '').lower()
    height = _safe_int(video_stream.get('height'))
    video_bitrate = _safe_int(video_stream.get('bit_rate'))
    total_bitrate = _safe_int(format_info.get('bit_rate'))
    bitrate = video_bitrate or total_bitrate
    duration = max(float(format_info.get('duration', 0) or 0), 1.0)
    size_mb = _safe_int(format_info.get('size')) / (1024 * 1024)

    if height >= 2160:
        very_low_kbps, low_kbps, high_kbps = 2400, 4000, 12000
    elif height >= 1080:
        very_low_kbps, low_kbps, high_kbps = 1100, 1800, 5500
    elif height >= 720:
        very_low_kbps, low_kbps, high_kbps = 650, 1000, 3000
    else:
        very_low_kbps, low_kbps, high_kbps = 380, 600, 1600

    bitrate_kbps = bitrate / 1000 if bitrate else 0
    is_hevc = codec in ('hevc', 'h265', 'x265')
    is_h264 = codec in ('h264', 'avc1')
    size_per_min_mb = size_mb / max(duration / 60.0, 1.0)

    if is_hevc and bitrate_kbps and bitrate_kbps <= very_low_kbps:
        return None, t('skip_hevc_low_bitrate', bitrate=bitrate_kbps, height=height or '?')

    if bitrate_kbps and bitrate_kbps <= max(350, very_low_kbps * 0.7):
        return None, t('skip_bitrate_too_low', bitrate=bitrate_kbps)

    if profile == 'medium':
        base_crf = 22
        min_crf, max_crf = 21, 24
    elif profile == 'high':
        base_crf = 23
        min_crf, max_crf = 22, 26
    else:
        base_crf = 24
        min_crf, max_crf = 24, 28

    if is_hevc:
        crf = base_crf
    elif is_h264:
        crf = base_crf
    else:
        crf = base_crf

    if height >= 2160:
        crf += 1
    elif height <= 720 and profile != 'medium':
        crf -= 1

    if bitrate_kbps >= high_kbps * 1.5:
        crf += 1 if profile == 'medium' else (2 if profile == 'high' else 3)
    elif bitrate_kbps >= high_kbps * 1.2:
        crf += 1 if profile == 'medium' else 2
    elif bitrate_kbps >= high_kbps:
        crf += 1
    elif bitrate_kbps and bitrate_kbps <= low_kbps:
        crf -= 1

    if size_per_min_mb >= 40:
        crf += 1 if profile == 'medium' else (2 if profile == 'high' else 2)
    elif size_per_min_mb >= 24:
        crf += 1
    elif size_per_min_mb <= 6:
        crf -= 1

    crf = max(min_crf, min(max_crf, crf))
    reason = (
        f"{codec or t('unknown_codec')}, {height or '?'}p, {bitrate_kbps:.0f} kbps, "
        f"{size_per_min_mb:.1f} MB/min"
    )
    return crf, reason

def human_size(n):
    for unit in ('B','KB','MB','GB'):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _sanitize_filename_part(name):
    name = re.sub(r'[\\/:*?"<>|]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip(" .-_")
    return name or "video"


def _extract_episode_code(name):
    patterns = [
        re.compile(r'(?i)\bS(\d{1,2})E(\d{1,3})\b'),
        re.compile(r'(?i)\b(\d{1,2})x(\d{1,3})\b'),
        re.compile(r'(?i)\bE(?:P)?(\d{1,3})\b'),
    ]
    for pattern in patterns:
        match = pattern.search(name)
        if not match:
            continue
        if len(match.groups()) == 2:
            return f"S{int(match.group(1)):02d}E{int(match.group(2)):02d}"
        return f"E{int(match.group(1)):02d}"
    return None


def build_clean_title(full_path):
    stem = Path(full_path).stem
    raw_name = stem
    raw_name = re.sub(r'(?i)\[[^\]]*?\]\((?:www\.)?[a-z0-9.-]+\.[a-z]{2,}\)', ' ', raw_name)
    name = re.sub(r'[\._]+', ' ', raw_name)
    name = re.sub(r'(?i)\b(www\.)?[a-z0-9-]+\.(com|net|org|info|biz|cc|to|me|tv|mx|io)\b', ' ', name)
    episode_code = _extract_episode_code(name)
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
    year = year_match.group(1) if year_match else None

    name = re.sub(r'[\[\(\{](?:[^\]\)\}]*?(?:2160p|1080p|720p|480p|x264|x265|h\.?264|h\.?265|hevc|bluray|brrip|bdrip|web[- ]?dl|webrip|hdrip|dvdrip|torrent|subs?|dub)[^\]\)\}]*)[\]\)\}]', ' ', name, flags=re.I)
    noise_pattern = re.compile(
        r'(?i)\b('
        r'2160p|1080p|720p|480p|x264|x265|h\.?264|h\.?265|hevc|av1|10bit|8bit|hdr|sdr|'
        r'bluray|brrip|bdrip|web[- ]?dl|webrip|hdrip|dvdrip|remux|proper|repack|'
        r'aac2?\.?0?|ac3|eac3|dts(?:-hd)?|truehd|atmos|mp3|flac|opus|'
        r'yify|rarbg|ettv|eztv|torrentgalaxy|tgx|psa|qxr|vyndros|'
        r'readnfo|internal|extended|uncut|limited|multi|subs?|dub|'
        r'mkv|mp4|avi|sample'
        r')\b'
    )
    name = noise_pattern.sub(' ', name)
    name = re.sub(r'(?i)\[(?:esp|spa|cast|lat|sub|eng|vose|vos|dual|multi)\]', ' ', name)

    if episode_code:
        name = re.sub(r'(?i)\bS\d{1,2}E\d{1,3}\b', ' ', name)
        name = re.sub(r'(?i)\b\d{1,2}x\d{1,3}\b', ' ', name)
        name = re.sub(r'(?i)\bE(?:P)?\d{1,3}\b', ' ', name)

    if year:
        name = re.sub(rf'\b{re.escape(year)}\b', ' ', name)

    name = re.sub(r'\(\s*\)', ' ', name)
    name = re.sub(r'\[\s*\]', ' ', name)
    name = re.sub(r'[-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip(" .-_")

    if episode_code:
        clean = f"{name} {episode_code}".strip()
    elif year:
        clean = f"{name} ({year})".strip() if name else year
    else:
        clean = name
    return _sanitize_filename_part(clean or stem)


def build_output_path(full_path, output_stem):
    suffix = Path(full_path).suffix
    base = os.path.dirname(full_path)
    path = os.path.join(base, f"{output_stem}{suffix}")
    n = 2
    while os.path.exists(path):
        path = os.path.join(base, f"{output_stem}_{n}{suffix}")
        n += 1
    return path


def safe_output_path(full_path):
    return build_output_path(full_path, f"{Path(full_path).stem}_compressed")


def summarize_video_plan(video_stream, format_info, crf):
    codec = (video_stream.get('codec_name') or '?').upper()
    width = _safe_int(video_stream.get('width'))
    height = _safe_int(video_stream.get('height'))
    bitrate = _safe_int(video_stream.get('bit_rate')) or _safe_int(format_info.get('bit_rate'))
    bitrate_kbps = bitrate / 1000 if bitrate else 0
    resolution = f"{width}x{height}" if width and height else t('unknown_resolution')
    return f"{codec}, {resolution}, {bitrate_kbps:.0f} kbps -> CRF {crf}"


def build_target_size_plan(format_info, audio_tracks, subtitle_tracks, target_size_mb):
    duration = max(float(format_info.get('duration', 0) or 0), 1.0)
    original_size_mb = _safe_int(format_info.get('size')) / (1024 * 1024)
    if original_size_mb and original_size_mb <= target_size_mb:
        return None, t('target_already_below', size=original_size_mb)

    target_total_kbps = max(300, int((target_size_mb * 8192) / duration))
    audio_kbps = estimate_audio_bitrate_kbps(audio_tracks)
    subtitle_overhead_kbps = 16 if subtitle_tracks else 0
    video_kbps = target_total_kbps - audio_kbps - subtitle_overhead_kbps - 24
    video_kbps = max(250, video_kbps)

    plan = {
        'kind': 'target_size',
        'target_size_mb': target_size_mb,
        'video_bitrate_k': video_kbps,
        'total_bitrate_k': target_total_kbps,
        'scale_height': 0,
    }
    reason = t('target_plan_reason', target=target_size_mb, video=video_kbps, audio=audio_kbps)
    return plan, reason


# ── Main ──────────────────────────────────────
def main():
    simulation_mode = '-S' in sys.argv[1:] or '--simulate' in sys.argv[1:]
    choose_ui_language()

    print(f"""\n{BOLD}{B}
      ______________________
     /_____________________/|
    |   .---------------.  ||
    |   |   VIDEO FILE  |  ||
    |   |   COMPRESS    |  ||
    |   '---------------'  ||
    |          ||          ||
    |          \\/          ||
    |        [====]        ||
    |______________________|/

 __     ___ ____  _____ ___   ____ ___  ____  _____ ____  
 \\ \\   / /|_ _|  _ \\| ____/ _ \\ / ___/ _ \\|  _ \\| ____|  _ \\ 
  \\ \\ / /  | || | | |  _|| | | | |  | | | | | | |  _| | |_) |
   \\ V /   | || |_| | |__| |_| | |__| |_| | |_| | |___|  _ < 
    \\_/   |___|____/|_____\\___/ \\____\\___/|____/|_____|_| \\_\\
{RST}""")
    if simulation_mode:
        print(f"{Y}{t('simulation_active')}{RST}\n")

    ensure_dependencies()

    encoder, gpu_label = detect_gpu_encoder()
    print(f"\n  {t('encoder')}: {BOLD}{gpu_label}{RST} ({encoder})")

    path = input(f"\n{BOLD}{t('input_folder')}{RST} ").strip().strip('"\'')
    if not os.path.isdir(path):
        print(f"\n{R}{t('invalid_path')}{RST}")
        return
    delete_original_if_better = ask_yes_no('delete_originals_q', default=False)
    smart_rename_enabled = ask_yes_no('smart_rename_q', default=False)

    videos = [
        os.path.join(root, f)
        for root, _, files in os.walk(path)
        for f in files
        if f.lower().endswith(SUPPORTED_EXT)
    ]
    if not videos:
        print(f"\n{Y}{t('no_videos')}{RST}")
        return

    print(f"\n  {G}{t('found_videos', count=len(videos))}{RST}")

    # ── Elegir modo ──
    print(f"\n  {BOLD}{t('selection_mode')}{RST}")
    print(f"   {C}[1]{RST} {t('mode_auto')}")
    print(f"   {C}[2]{RST} {t('mode_manual')}")
    while True:
        modo = input(t('choose_mode')).strip()
        if modo in ('1', '2'):
            break
        print(f"  {R}{t('invalid_1_2')}{RST}")

    auto_profile = choose_auto_profile() if modo == '1' else None
    cleanup_tracks = ask_yes_no('track_cleanup_q', default=True) if modo == '1' else False
    target_langs = None
    if modo == '1' and cleanup_tracks:
        target_langs = choose_target_langs()

    crf = ask_crf() if modo == '2' else None
    total_saved = 0

    for full_path in videos:
        file = os.path.basename(full_path)
        print(f"\n{BOLD}{'─'*52}")
        print(f"  📁  {file}{RST}")
        clean_title = build_clean_title(full_path) if smart_rename_enabled else None
        if clean_title:
            print(f"  {DIM}{t('smart_rename_preview', name=clean_title)}{RST}")

        try:
            info = get_video_info(full_path)
        except RuntimeError as e:
            print(f"  {R}{t('analysis_error', error=e)}{RST}")
            continue

        streams  = info.get('streams', [])
        format_info = info.get('format', {})
        duration = float(format_info.get('duration', 0))

        v_idx  = None
        video_stream = None
        audios = []
        subs   = []
        for s in streams:
            idx   = s['index']
            lang  = s.get('tags', {}).get('language', 'und')
            title = s.get('tags', {}).get('title', '')
            codec = s.get('codec_name', '?')
            forced = bool(s.get('disposition', {}).get('forced', 0))
            default = bool(s.get('disposition', {}).get('default', 0))
            extra = f"{codec}  {title}".strip()
            if s['codec_type'] == 'video' and v_idx is None:
                v_idx = idx
                video_stream = s
            elif s['codec_type'] == 'audio':
                audios.append({
                    'index': idx,
                    'lang': lang,
                    'extra': extra,
                    'codec': codec,
                    'bit_rate': s.get('bit_rate'),
                    'channels': s.get('channels'),
                    'channel_layout': s.get('channel_layout'),
                    'default': default,
                })
            elif s['codec_type'] == 'subtitle':
                subs.append({
                    'index': idx,
                    'lang': lang,
                    'extra': extra,
                    'codec': codec,
                    'forced': forced,
                    'default': default,
                })

        if v_idx is None or video_stream is None:
            print(f"  {R}{t('no_video_track')}{RST}")
            continue

        if modo == '1' and cleanup_tracks and target_langs:
            selected_a, selected_s = auto_select_tracks(audios, subs, target_langs, file)
        else:
            if modo == '1':
                selected_a = [track['index'] for track in audios]
                selected_s = [track['index'] for track in subs]
            else:
                selected_a = pick_tracks(t('audio_tracks_label'), audios)
                selected_s = pick_tracks(t('subtitle_tracks_label'), subs, allow_none=True)

        if not selected_a:
            print(f"  {Y}{t('no_audio_default')}{RST}")
            selected_a = [audios[0]['index']] if audios else []

        source_height = _safe_int(video_stream.get('height'))
        encode_plan = {'kind': 'crf', 'crf': crf, 'scale_height': 0}
        target_size_mb = None
        if modo == '1':
            if auto_profile == 'target':
                original_mb = _safe_int(format_info.get('size')) / (1024 * 1024)
                target_default = max(120, int(round(original_mb * 0.45))) if original_mb else 120
                target_size_mb = ask_target_size_mb(default=target_default)
            else:
                current_crf, reason = choose_auto_crf(video_stream, format_info, auto_profile)
                if current_crf is None:
                    print(f"  {Y}{t('skip_recompression', reason=reason)}{RST}")
                    continue
                auto_scale, scale_reason = choose_auto_scale(video_stream, format_info, current_crf, auto_profile)
                encode_plan = {'kind': 'crf', 'crf': current_crf, 'scale_height': auto_scale}
                print(f"  {C}{t('profile_label')}:{RST} {auto_profile_label(auto_profile)}")
                print(f"  {C}{t('automatic_decision')}{RST} {summarize_video_plan(video_stream, format_info, current_crf)}")
                print(f"  {DIM}{t('reason', reason=reason)}{RST}")
                print(f"  {DIM}{t('resolution_label')}: {summarize_scale(auto_scale)} ({scale_reason}){RST}")

        selected_audio_tracks = []
        audio_by_index = {track['index']: track for track in audios}
        for idx in selected_a:
            if idx in audio_by_index:
                track = dict(audio_by_index[idx])
                track['copy_ok'] = should_copy_audio(track)
                selected_audio_tracks.append(track)

        selected_subtitle_tracks = []
        sub_by_index = {track['index']: track for track in subs}
        for idx in selected_s:
            if idx in sub_by_index:
                selected_subtitle_tracks.append(dict(sub_by_index[idx]))

        default_audio = _pick_default_track(audios, selected_a)
        if default_audio:
            selected_audio_tracks.sort(key=lambda track: 0 if track['index'] == default_audio['index'] else 1)

        print(f"  {C}{t('audio')}:{RST} {summarize_audio_plan(selected_audio_tracks)}")
        print(f"  {C}{t('subs')}:{RST} {summarize_subtitle_plan(selected_subtitle_tracks)}")

        if modo == '1' and auto_profile == 'target':
            encode_plan, reason = build_target_size_plan(
                format_info, selected_audio_tracks, selected_subtitle_tracks, target_size_mb
            )
            if encode_plan is None:
                print(f"  {Y}{t('skip_recompression', reason=reason)}{RST}")
                continue
            target_scale, scale_reason = choose_target_scale(
                video_stream, target_size_mb, encode_plan['total_bitrate_k']
            )
            encode_plan['scale_height'] = target_scale
            print(f"  {C}{t('profile_label')}:{RST} {auto_profile_label(auto_profile)}")
            print(f"  {C}{t('target_size_label')}:{RST} {target_size_mb:.1f} MB")
            print(f"  {DIM}{reason}.{RST}")
            print(f"  {DIM}{t('resolution_label')}: {summarize_scale(target_scale)} ({scale_reason}){RST}")
        elif modo == '2':
            manual_scale = ask_resolution_target(source_height)
            encode_plan['scale_height'] = manual_scale

        output_stem = f"{clean_title}_compressed" if clean_title else f"{Path(full_path).stem}_compressed"
        out_path  = build_output_path(full_path, output_stem)
        orig_size = os.path.getsize(full_path)
        print(f"\n  {DIM}{t('original_size', size=human_size(orig_size))}{RST}")

        if simulation_mode:
            print(f"  {Y}{t('simulation_output', path=out_path)}{RST}")
            continue

        print(f"  {G}{t('compressing')}{RST}")

        try:
            ok = compress_video(full_path, out_path, v_idx, selected_audio_tracks, selected_subtitle_tracks,
                                encoder, encode_plan, duration)
        except RuntimeError as e:
            print(f"  {R}{t('fatal_error', error=e)}{RST}")
            continue

        if ok and os.path.exists(out_path):
            new_size = os.path.getsize(out_path)
            if new_size >= orig_size:
                os.remove(out_path)
                print(f"  {Y}{t('discarded_bigger')}{RST}")
                continue
            saved    = orig_size - new_size
            pct      = (saved / orig_size * 100) if orig_size else 0
            total_saved += saved
            color = G if saved > 0 else Y
            print(f"  {color}{t('saved_ok', size=human_size(new_size), pct=pct, saved=human_size(abs(saved)))}{RST}")
            print(f"  {DIM}{t('saved_path', path=out_path)}{RST}")
            if delete_original_if_better and os.path.exists(full_path):
                final_path = out_path
                os.remove(full_path)
                if clean_title:
                    desired_path = build_output_path(full_path, clean_title)
                    if os.path.abspath(desired_path) != os.path.abspath(out_path):
                        os.replace(out_path, desired_path)
                        final_path = desired_path
                        print(f"  {DIM}{t('final_renamed', path=final_path)}{RST}")
                print(f"  {Y}{t('deleted_original')}{RST}")
        else:
            print(f"  {R}{t('ffmpeg_error_file', file=file)}{RST}")

    if total_saved > 0:
        print(f"\n{BOLD}{G}{t('total_saved', size=human_size(total_saved))}{RST}\n")
    else:
        print(f"\n{Y}{t('process_finished')}{RST}\n")


if __name__ == "__main__":
    main()
