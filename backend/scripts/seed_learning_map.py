"""Migration script to create and seed Learning Map progress data.

Usage:
    python backend/scripts/seed_learning_map.py [--force]
    
Options:
    --force  Recreate all progress records even if they exist
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session
from frontend.core.database import engine, create_db_and_tables
from frontend.services.learning_map_service import LearningMapService
from frontend.models.learning_progress import LearningProgress, MapStatus, MapRegion


def main():
    """Create learning_progress table and seed initial data."""
    print("🗺️ Learning Map Migration")
    print("=" * 50)
    
    # Parse args
    force = "--force" in sys.argv
    
    # Create tables (will create learning_progress if not exists)
    print("\n📦 Creating tables...")
    create_db_and_tables()
    print("   ✅ Tables created/verified")
    
    # Seed progress data
    print("\n🌱 Seeding progress data...")
    service = LearningMapService()
    
    try:
        count = service.seed_progress(force=force)
        
        if count > 0:
            print(f"   ✅ Created {count} progress records")
        else:
            print("   ℹ️  Progress records already exist (use --force to recreate)")
        
        # Show stats
        print("\n📊 Region Statistics:")
        print("-" * 50)
        
        for region in MapRegion:
            stats = service.get_region_stats(region)
            print(f"   {stats['icon']} {stats['region_name']}: "
                  f"{stats['total']} items "
                  f"({stats['available']} available, {stats['locked']} locked)")
        
        # Overall stats
        overall = service.get_overall_stats()
        print("-" * 50)
        print(f"   📈 Total: {overall['total']} grammar items")
        print(f"   🔓 Available to learn: {overall['available']}")
        print(f"   🔒 Locked: {overall['locked']}")
        
    finally:
        service.close()
    
    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
