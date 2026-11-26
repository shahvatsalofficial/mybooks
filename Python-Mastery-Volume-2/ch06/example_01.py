extra_compile_args = [
    "-O3",                      # Maximum optimization
    "-march=native",            # Generates AVX2 / AVX-512 vector instructions for the host CPU
    "-ffast-math",              # Enables aggressive floating-point reassociation
    "-fomit-frame-pointer",     # Frees up a general-purpose register
]
