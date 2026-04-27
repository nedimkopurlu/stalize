"""
Initial Data Load Script
İlk kurulumda BIST100 verilerini yükler.
Kullanım: python3 -m scripts.initial_load
"""
import asyncio
import logging
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_collector import data_collector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


async def main():
    print("=" * 60)
    print("  Stalize — İlk Veri Yüklemesi")
    print("=" * 60)
    print()

    await data_collector.full_initial_load()

    print()
    print("=" * 60)
    print("  ✅ Yükleme tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
