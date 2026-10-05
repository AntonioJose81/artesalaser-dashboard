#!/usr/bin/env python3
"""Calcula el coste de API (DeepSeek/MiniMax) de la semana a partir de `hermes insights`.

Convencion del dashboard ARTESALASER: se toma el TOTAL de tokens de todos los
modelos y se aplica el precio blended de DeepSeek V4 Pro (80% input / 20% output),
es decir 0.522 $/M tokens.
"""
import subprocess, re, sys
from datetime import datetime

# Precios por millon de tokens (USD)
PRICES = {
    'deepseek-v4-pro':   {'input': 0.435, 'output': 0.87},
    'deepseek-reasoner': {'input': 0.55,  'output': 2.19},
    'minimax-m3':        {'input': 0.30,  'output': 1.20},
}

# Los modelos que realmente usa Hermes -> precio a aplicar
ALIASES = {
    'deepseek-v4-pro':   'deepseek-v4-pro',
    'deepseek-v4-flash': 'deepseek-v4-pro',   # flash se factura al precio V4 Pro (convencion dashboard)
    'deepseek-flash':    'deepseek-v4-pro',
    'deepseek-reasoner': 'deepseek-reasoner',
    'minimax-m3':        'minimax-m3',
}

INPUT_SHARE = 0.8
OUTPUT_SHARE = 0.2


def main():
    result = subprocess.run(['hermes', 'insights', '--days', '7'], capture_output=True, text=True)
    output = result.stdout

    # Extraer tokens por modelo de la tabla "Models Used"
    model_tokens = {}
    for line in output.split('\n'):
        m = re.match(r'\s*([A-Za-z0-9._-]+)\s+(\d+)\s+([\d,]+)\s*$', line)
        if m and not m.group(1).lower().startswith('model'):
            model_tokens[m.group(1)] = int(m.group(3).replace(',', ''))

    if not model_tokens:
        print('ERROR: no se han podido parsear los modelos de hermes insights')
        return 1

    # El total del dashboard usa TODOS los tokens (incl. modelos sin precio propio)
    total_tokens = sum(model_tokens.values())

    # Precio blended de V4 Pro como referencia unica (convencion dashboard)
    ref = PRICES['deepseek-v4-pro']
    blended = INPUT_SHARE * ref['input'] + OUTPUT_SHARE * ref['output']
    cost = total_tokens / 1_000_000 * blended

    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    for model, tokens in model_tokens.items():
        print(f"  {model}: {tokens:,} tokens")
    print(f"TOTAL tokens: {total_tokens:,} ({total_tokens/1e6:.1f}M)")
    print(f"Precio blended: ${blended:.3f}/M")
    print(f"COSTE ESTIMADO: ${cost:.2f}")
    print()
    print('Entrada a anadir en const gastos (index.html):')
    print(f'  {{fecha:"{datetime.now().strftime("%Y-%m-%d")}",proveedor:"DeepSeek",'
          f'concepto:"API Hermes {total_tokens/1e6:.1f}M tokens '
          f'(sem {(datetime.now()).strftime("%d %b")})",categoria:"API",'
          f'base_imponible:{round(cost,2):.2f},iva:0.00,total:{round(cost,2):.2f},justificante:""}},')
    return 0


if __name__ == '__main__':
    sys.exit(main())
