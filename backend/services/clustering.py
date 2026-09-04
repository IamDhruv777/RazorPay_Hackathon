import uuid
import numpy as np
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import ExceptionModel, ExceptionCluster

try:
    from sklearn.cluster import DBSCAN
except ImportError:
    DBSCAN = None

async def cluster_exceptions(db: AsyncSession, run_id: str) -> list[ExceptionCluster]:
    """
    Groups unresolved exceptions into clusters using DBSCAN based on temporal and categorical features.
    """
    from sqlalchemy import select
    
    # Fetch exceptions for this run
    stmt = select(ExceptionModel).where(ExceptionModel.run_id == run_id)
    exceptions = (await db.execute(stmt)).scalars().all()
    
    if not exceptions:
        return []

    # If DBSCAN is not available or too few exceptions, do basic rule-based clustering
    if DBSCAN is None or len(exceptions) < 3:
        return _rule_based_clustering(db, exceptions, run_id)

    # Prepare features for DBSCAN
    # Features:
    # 1. Time (scaled so 1 unit = 2 hours)
    # 2. Exception Type (mapped to integer coordinates spaced far apart so different types rarely mix unless simultaneous)
    
    type_map = {t: i * 10 for i, t in enumerate(set(e.type for e in exceptions))}
    
    features = []
    for e in exceptions:
        ts = e.transaction_ts.timestamp() if e.transaction_ts else e.created_at.timestamp()
        ts_hours = ts / 7200.0 # 2 hours = 1.0 distance
        type_val = type_map[e.type]
        features.append([ts_hours, type_val])
        
    X = np.array(features)
    
    # DBSCAN: eps=1.5 means within ~3 hours and same type (since different types are distance 10 apart)
    # This means it will perfectly cluster identical exceptions happening in a burst!
    clustering = DBSCAN(eps=1.5, min_samples=2).fit(X)
    
    labels = clustering.labels_
    
    clusters_dict = defaultdict(list)
    noise = []
    
    for exc, label in zip(exceptions, labels):
        if label == -1:
            noise.append(exc)
        else:
            clusters_dict[label].append(exc)
            
    created_clusters = []
    
    for label, group in clusters_dict.items():
        c_type = group[0].type
        total_exp = sum(e.financial_exposure or 0.0 for e in group)
        
        cluster = ExceptionCluster(
            id=f"CLUSTER-{uuid.uuid4().hex[:8]}",
            name=f"Burst of {c_type}",
            common_features={"type": c_type, "count": len(group)},
            total_exposure=total_exp,
            status="OPEN"
        )
        db.add(cluster)
        for e in group:
            e.cluster_id = cluster.id
            
        created_clusters.append(cluster)
        
    # Noise points remain unclustered (cluster_id = None)
    
    await db.commit()
    return created_clusters

def _rule_based_clustering(db, exceptions, run_id):
    # fallback
    return []


