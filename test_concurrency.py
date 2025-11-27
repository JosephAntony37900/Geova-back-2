"""
Script de prueba de concurrencia para verificar mejoras de threading.
Ejecutar mientras el servidor está corriendo para probar que no se bloquea.
"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def test_concurrent_requests(url: str, num_requests: int = 20):
    """
    Prueba requests concurrentes para verificar que la API no se bloquea.
    """
    print(f"\n🧪 Probando {num_requests} requests concurrentes a {url}")
    print("=" * 60)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        async def make_request(i):
            req_start = time.time()
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    req_time = time.time() - req_start
                    status = response.status
                    data = await response.json()
                    return {
                        'id': i,
                        'status': status,
                        'time': req_time,
                        'success': status == 200,
                        'data': data
                    }
            except asyncio.TimeoutError:
                return {
                    'id': i,
                    'status': 'TIMEOUT',
                    'time': time.time() - req_start,
                    'success': False,
                    'error': 'Timeout'
                }
            except Exception as e:
                return {
                    'id': i,
                    'status': 'ERROR',
                    'time': time.time() - req_start,
                    'success': False,
                    'error': str(e)
                }
        
        # Ejecutar todas las requests en paralelo
        tasks = [make_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Análisis de resultados
    successful = sum(1 for r in results if r['success'])
    failed = num_requests - successful
    avg_time = sum(r['time'] for r in results) / num_requests
    min_time = min(r['time'] for r in results)
    max_time = max(r['time'] for r in results)
    
    print(f"\n📊 Resultados:")
    print(f"  ✅ Exitosas:     {successful}/{num_requests} ({successful/num_requests*100:.1f}%)")
    print(f"  ❌ Fallidas:     {failed}/{num_requests}")
    print(f"  ⏱️  Tiempo total:  {total_time:.2f}s")
    print(f"  📈 Requests/seg:  {num_requests/total_time:.2f}")
    print(f"\n⏱️  Tiempos de respuesta:")
    print(f"  • Promedio: {avg_time:.3f}s")
    print(f"  • Mínimo:   {min_time:.3f}s")
    print(f"  • Máximo:   {max_time:.3f}s")
    
    # Mostrar detalles de requests lentos
    slow_requests = [r for r in results if r['time'] > 2.0]
    if slow_requests:
        print(f"\n⚠️  Requests lentos (>2s): {len(slow_requests)}")
        for r in slow_requests[:5]:  # Mostrar solo los primeros 5
            print(f"  • Request #{r['id']}: {r['time']:.2f}s - {r.get('status', 'ERROR')}")
    
    return results

async def test_health_during_capture():
    """
    Prueba que /health responda mientras se capturan fotos en IMX477.
    ANTES: /health tardaba 5s (bloqueado por captura)
    AHORA: /health debe responder <1s
    """
    print(f"\n🧪 Probando respuesta de /health durante captura de fotos")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Disparar captura de IMX477 (tarda 5s)
        imx_task = asyncio.create_task(session.get('http://localhost:8000/imx477/sensor'))
        
        # Esperar 1s y luego probar /health
        await asyncio.sleep(1)
        
        health_start = time.time()
        async with session.get('http://localhost:8000/health') as response:
            health_time = time.time() - health_start
            health_data = await response.json()
        
        # Esperar a que termine captura IMX
        await imx_task
        
        if health_time < 2.0:
            print(f"  ✅ /health respondió en {health_time:.3f}s (NO bloqueado)")
        else:
            print(f"  ❌ /health tardó {health_time:.3f}s (posible bloqueo)")
        
        return health_time < 2.0

async def test_sequential_vs_parallel():
    """
    Compara tiempo secuencial vs paralelo para IMX477.
    """
    print(f"\n🧪 Comparando ejecución secuencial vs paralela")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Test secuencial
        print("  📋 Secuencial (5 requests una por una)...")
        seq_start = time.time()
        for i in range(5):
            await session.get('http://localhost:8000/imx477/sensor')
        seq_time = time.time() - seq_start
        
        # Test paralelo
        print("  ⚡ Paralelo (5 requests simultáneas)...")
        par_start = time.time()
        tasks = [session.get('http://localhost:8000/imx477/sensor') for _ in range(5)]
        await asyncio.gather(*tasks)
        par_time = time.time() - par_start
        
        print(f"\n  📊 Resultados:")
        print(f"    • Secuencial: {seq_time:.2f}s ({seq_time/5:.2f}s por request)")
        print(f"    • Paralelo:   {par_time:.2f}s ({par_time/5:.2f}s por request)")
        print(f"    • Mejora:     {seq_time/par_time:.2f}x más rápido")
        
        if par_time < seq_time * 0.7:  # Esperamos >30% de mejora
            print(f"    ✅ Threading funciona correctamente!")
        else:
            print(f"    ⚠️  Mejora menor a esperada (posible problema)")

async def main():
    """
    Suite completa de pruebas de concurrencia.
    """
    print("\n" + "="*60)
    print("🚀 SUITE DE PRUEBAS DE CONCURRENCIA")
    print("="*60)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test 1: Health endpoint durante captura
        print("\n" + "-"*60)
        print("TEST 1: Verificar que /health no se bloquea")
        print("-"*60)
        await test_health_during_capture()
        
        # Test 2: Requests concurrentes a /health
        print("\n" + "-"*60)
        print("TEST 2: Requests concurrentes a /health")
        print("-"*60)
        await test_concurrent_requests('http://localhost:8000/health', num_requests=50)
        
        # Test 3: Requests concurrentes a IMX477
        print("\n" + "-"*60)
        print("TEST 3: Requests concurrentes a IMX477")
        print("-"*60)
        await test_concurrent_requests('http://localhost:8000/imx477/sensor', num_requests=10)
        
        # Test 4: Secuencial vs Paralelo
        print("\n" + "-"*60)
        print("TEST 4: Comparación secuencial vs paralela")
        print("-"*60)
        await test_sequential_vs_parallel()
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error en pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  IMPORTANTE: Asegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("   Ejecutar: python main.py\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas canceladas por usuario")
