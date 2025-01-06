from os import system, environ

__all__ = 'print_gpu_info',


def print_gpu_info():
    # Tensorflow Log Level
    # 0 = all messages are logged (default behavior)
    # 1 = INFO messages are not printed
    # 2 = INFO and WARNING messages are not printed
    # 3 = INFO, WARNING, and ERROR messages are not printed
    environ['TF_CPP_MIN_LOG_LEVEL'] = '1'

    # Tensorflow darf wegen Multiprocessing nicht im Hauptprozess importiert werden.
    # Ansonsten würde ein Fork z.B. den GPU-RAM teilen wollen, das kann aber nicht funktionieren.
    import tensorflow as tf

    system('nvidia-smi')
    print()
    print(f'Anzahl GPUs: {len(tf.config.experimental.list_physical_devices("GPU"))}')
    print(f'GPU Device Name: {tf.test.gpu_device_name()}')
