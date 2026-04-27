import asyncio
import sys
import os

# Add main dir to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_collector import data_collector

async def main():
    print("Collecting fundamentals...")
    await data_collector.collect_fundamentals()
    
    # After fundamentals are loaded, run scoring manually to recalculate overall_scores
    from app.services.scoring import scoring_engine
    print("Recalculating overall scores...")
    await scoring_engine.update_all_scores()
    
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())
