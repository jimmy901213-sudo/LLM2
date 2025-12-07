"""
搜索模塊：為主程式提供產品搜索與檢索器上下文彙整的輔助函數
支持關鍵字搜索與語義搜索（模糊語言理解）
支持Category-Aware搜索權重
"""
from typing import List, Optional, Dict, Any

# ========== CATEGORY MAPPING & KEYWORDS ==========
# 根據product category建立keyword映射，用於query→category推理
CATEGORY_KEYWORDS = {
    "音頻設備": ["喇叭", "音箱", "音響", "speaker", "耳機", "headphone", "earbud", "麥克風", "mic", "音頻"],
    "家具": ["椅子", "椅", "桌子", "桌", "沙發", "床", "家具", "furniture"],
    "生活家電": ["風扇", "清淨", "機器人", "掃地", "清潔", "消毒", "盒"],
    "電腦周邊": ["鍵盤", "滑鼠", "鼠標", "顯示器", "monitor", "鍵", "keyboard", "mouse", "周邊", "護眼", "螢幕燈", "螢幕掛燈", "護眼燈", "護目"],
    "穿戴式裝置": ["手錶", "手環", "智能", "穿戴", "wearable", "watch", "band"],
    "家庭娛樂": ["投影", "投影機", "cinema", "螢幕", "顯示", "娛樂"],
    "儲存設備": ["ssd", "硬碟", "存儲", "儲存", "storage", "硬盤"],
    "廚房家電": ["咖啡", "咖啡機", "coffee", "廚房"],
    "個人護理": ["牙刷", "吹風機", "護理", "美容"],
    "手機配件": ["電源", "行動", "手機", "充電", "配件"],
    "網路設備": ["路由器", "wifi", "網路", "router"],
    "攝影器材": ["攝影機", "相機", "camera"],
    "智慧家居": ["門鈴", "智能", "智慧", "smart", "home"],
    "運動器材": ["瑜珈", "運動", "sport"],
}

def extract_category_keywords_from_query(query: str) -> List[str]:
    """
    從查詢中提取相關的category keywords
    例如："防水的藍牙喇叭" → ["喇叭", "藍牙"]
    """
    query_lower = query.lower()
    found_keywords = []
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                found_keywords.append(keyword)
    
    return list(set(found_keywords))  # 去重

def infer_target_categories_from_query(query: str) -> List[str]:
    """
    從查詢推理目標category列表
    例如："防水的藍牙喇叭" → ["音頻設備", "戶外使用"]
    """
    query_lower = query.lower()
    target_categories = set()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in query_lower:
                target_categories.add(category)
    
    return list(target_categories)

def calculate_category_weight(product_category: str, target_categories: List[str], boost_keywords: Optional[List[str]] = None) -> float:
    """
    計算該產品應該獲得的category權重
    同category產品: 2.0x
    相關category產品: 1.3x
    無關category產品: 0.7x
    
    Args:
        product_category: 產品的category
        target_categories: 從query推理出的目標categories
        boost_keywords: 額外的boost keywords
    
    Returns:
        權重乘數 (0.5 ~ 2.0)
    """
    if not target_categories:
        # 如果無法推理出target categories，返回中立權重
        return 1.0
    
    # 完全匹配: 2.0x
    if product_category in target_categories:
        return 2.0
    
    # 檢查是否有部分相關性
    # 例如：產品是"音頻設備"，query涉及"戶外"相關
    related_boost = 1.0
    
    # 若product是"家電"，且query涉及"清潔"，給予boost
    if "生活家電" in product_category or "生活家電" in target_categories:
        related_boost = 1.3
    
    # 若product是"音頻"，且query涉及"防水"等相關特性
    if any("音頻" in cat or "喇叭" in cat for cat in target_categories):
        if "音頻" in product_category or "喇叭" in product_category:
            return 2.0
    
    # 投影機會被誤判為"光源"相關產品，需要特殊處理
    if "家庭娛樂" in target_categories and "投影" in product_category:
        # 只有查詢明確包含"投影"或"螢幕"時才boost投影機
        return 1.5
    
    # 無關category: 0.7x (降權防止overfitting)
    return 0.7


def is_product_matching_categories(metadata: Dict[str, Any], target_categories: List[str]) -> bool:
    """
    根據產品的metadata (name, description, category, features) 判斷該產品是否屬於任一 target_categories。
    - 優先使用 metadata['category']。
    - 其次檢查 product_name、description、features 中是否包含任何該 category 的關鍵詞。
    返回 True 表示該產品可視為屬於目標category。
    """
    if not target_categories:
        return True

    # 檢查明確的category欄位
    prod_cat = (metadata.get('category') or "").strip()
    if prod_cat and prod_cat in target_categories:
        return True

    # 蒐集產品可檢查文字
    content_candidates = []
    for k in ('product_name', 'name', 'description', 'features'):
        v = metadata.get(k)
        if isinstance(v, list):
            content_candidates.append(' '.join(v))
        elif isinstance(v, str):
            content_candidates.append(v)

    content_lower = ' '.join(content_candidates).lower()

    # 若任何一個 target category 的關鍵字出現在內容中，視為匹配
    for cat in target_categories:
        keywords = CATEGORY_KEYWORDS.get(cat, [])
        for kw in keywords:
            if kw.lower() in content_lower:
                return True

    return False


def compute_category_match_score(metadata: Dict[str, Any], target_categories: List[str]) -> float:
    """
    計算產品與目標categories之間的匹配度，返回 0.0~1.0。
    - 如果metadata['category']精確匹配任一target -> 1.0
    - 否則檢查product name/description/features中出現的category關鍵詞數量，基於出現次數產生score。
    這個評分用於在融合階段穩健地提升或過濾與查詢語意不符的產品，避免針對個別產品的硬編碼。
    """
    if not target_categories:
        return 1.0

    prod_cat = (metadata.get('category') or "").strip()
    if prod_cat and prod_cat in target_categories:
        return 1.0

    # collect text to search
    content_parts = []
    for k in ('product_name', 'name', 'description', 'features'):
        v = metadata.get(k)
        if isinstance(v, list):
            content_parts.append(' '.join(v))
        elif isinstance(v, str):
            content_parts.append(v)
    content = ' '.join(content_parts).lower()

    total_hits = 0
    total_possible = 0
    for cat in target_categories:
        kw_list = CATEGORY_KEYWORDS.get(cat, [])
        if not kw_list:
            continue
        total_possible += len(kw_list)
        for kw in kw_list:
            if kw.lower() in content:
                total_hits += 1

    if total_possible == 0:
        # no keywords known for these categories — fallback to permissive match
        return 0.5

    # normalize hits into 0..1, cap influence so that a few matches can still be meaningful
    normalized = min(1.0, total_hits / max(1, min(total_possible, 4)))
    return float(normalized)


def compute_attribute_match_score(metadata: Dict[str, Any], query: str) -> float:
    """
    計算產品對query中提及的特定屬性的匹配度。
    例如：query="防水的藍牙喇叭"，會檢查產品features是否包含"防水"。
    返回 0.0~1.0；高分表示產品有符合query提及的特定屬性。
    
    屬性關鍵字包括：防水、降噪、快充、續航、etc.
    """
    ATTRIBUTE_KEYWORDS = {
        "防水": ["防水", "waterproof"],  # 移除"ipx"因為會誤匹配耳機的IPX4
        "降噪": ["降噪", "noise-canceling", "anc"],
        "快充": ["快充", "快速充電", "quick charge", "fast"],
        "續航": ["續航", "battery", "長效", "endurance"],
        "護眼": ["護眼", "護目", "防藍光", "blue light"],
        "高清": ["4k", "8k", "高清", "高精", "ultra"],
        "輕量": ["輕", "小", "compact", "portable"],
        "靜音": ["靜音", "無聲", "quiet", "silent"],
    }

    query_lower = query.lower()
    
    # 蒐集產品特徵文本
    features = metadata.get('features', [])
    if isinstance(features, list):
        features_str = ' '.join(features).lower()
    else:
        features_str = (features or "").lower()
    
    name = (metadata.get('name') or metadata.get('product_name') or "").lower()
    description = (metadata.get('description') or "").lower()
    product_text = f"{name} {description} {features_str}".lower()

    # 檢查query中提及的屬性keyword是否出現在產品信息中
    matched_attrs = 0
    total_attrs = 0

    for attr_name, attr_keywords in ATTRIBUTE_KEYWORDS.items():
        for attr_keyword in attr_keywords:
            if attr_keyword.lower() in query_lower:
                # query提及此屬性
                total_attrs += 1
                if attr_keyword.lower() in product_text:
                    # 產品也有此屬性
                    matched_attrs += 1
                break  # 每個屬性只檢查一次

    if total_attrs == 0:
        # query中沒有提及特定屬性，返回中立值
        return 0.5

    # 返回匹配的屬性佔比，0.0~1.0
    return float(matched_attrs / max(1, total_attrs))


def compute_product_type_match_score(metadata: Dict[str, Any], query: str) -> float:
    """
    計算產品型號/名稱是否與query中提及的特定產品類型匹配。
    例如：query="防水的藍牙喇叭" → 應該優先匹配包含"喇叭"的產品，而非"耳機"。
    
    PRODUCT_TYPES定義了常見的產品子類型詞彙（比category更細粒度）。
    返回 0.0~1.0；高分表示產品型號精確匹配query提及的產品類型。
    """
    PRODUCT_TYPES = {
        "喇叭": ["喇叭", "speaker", "音箱"],
        "耳機": ["耳機", "earbuds", "headphones", "pods", "earbud"],
        "麥克風": ["麥克風", "microphone", "mic"],
        "椅子": ["椅子", "椅", "chair"],
        "鍵盤": ["鍵盤", "keyboard"],
        "滑鼠": ["滑鼠", "鼠標", "mouse"],
        "顯示器": ["顯示器", "monitor", "螢幕"],
        "手錶": ["手錶", "watch"],
        "投影": ["投影", "投影機", "projector"],
    }

    query_lower = query.lower()
    
    # 蒐集產品名稱文本
    product_name = (metadata.get('name') or metadata.get('product_name') or "").lower()
    
    # 檢查query中提及的產品類型是否出現在產品名稱中
    for product_type, type_keywords in PRODUCT_TYPES.items():
        for type_keyword in type_keywords:
            if type_keyword.lower() in query_lower:
                # query提及此產品類型
                if type_keyword.lower() in product_name:
                    # 產品名稱包含此類型 -> 強匹配
                    return 1.0
                break

    # 如果query提及特定產品類型，但產品名稱不包含，則返回低分
    for product_type, type_keywords in PRODUCT_TYPES.items():
        for type_keyword in type_keywords:
            if type_keyword.lower() in query_lower:
                # query提及此產品類型，但產品名稱不包含 -> 弱匹配
                return 0.3
    
    # query沒有提及特定產品類型，返回中立值
    return 0.6

def semantic_search_products(
    vectorstore_updater,
    query: str,
    limit: int = 10,
    score_threshold: float = 0.2,
    product_only: bool = True,
    boost_keywords: Optional[List[str]] = None,
    enable_category_weight: bool = True
) -> List[Dict[str, Any]]:
    """
    基於向量相似度的語義搜索，支持關鍵詞增強和Category-Aware權重
    支持自然語言查詢，例如：
    - "適合海邊的藍牙音響"
    - "每日使用的電子產品"
    - "能保護眼睛的螢幕燈"
    
    Args:
        vectorstore_updater: VectorstoreUpdater 實例
        query: 自然語言查詢字符串
        limit: 最多返回結果數
        score_threshold: 相似度分數閾值（0~1），過低的結果會被過濾
        product_only: 如果為 True，只返回產品（過濾規則文檔）
        boost_keywords: 可選的關鍵詞列表，用於提升結果排名
        enable_category_weight: 是否啟用category-aware權重 (預設True)
        
    Returns:
        包含產品資訊和相似度分數的字典列表，已按相似度排序
    """
    if vectorstore_updater is None:
        return []
    
    try:
        vectorstore = vectorstore_updater.vectorstore
        
        # 推理目標categories
        target_categories = infer_target_categories_from_query(query) if enable_category_weight else []
        
        # 使用向量庫的相似度搜索（基於嵌入向量）
        # 如果 product_only=True，取得更多結果以過濾規則文檔
        search_limit = limit * 3 if product_only else limit
        results = vectorstore.similarity_search_with_relevance_scores(query, k=search_limit)
        
        output = []
        for doc, score in results:
            # 跳過低相似度結果
            if score < score_threshold:
                continue
            
            # 提取元數據與內容
            metadata = doc.metadata or {}
            
            # 若只要產品，過濾掉規則文檔（source != "product_db"）
            if product_only:
                source = metadata.get("source", "")
                if source != "product_db":
                    continue

            # 嚴格分類過濾：如果推理出target_categories，且該產品不匹配其中任何category，則跳過
            if enable_category_weight and target_categories:
                if not is_product_matching_categories(metadata, target_categories):
                    continue
            
            product_name = (
                metadata.get("product_name")
                or metadata.get("name")
                or metadata.get("product_id")
                or "Unknown"
            )
            category = metadata.get("category", "")
            price = metadata.get("price", "")
            
            # 計算最終分數
            final_score = score
            
            # 計算產品與目標category的匹配度，並用於過濾或微調分數。
            match_score = 1.0
            if enable_category_weight and target_categories:
                match_score = compute_category_match_score(metadata, target_categories)
                # 如果匹配度極低(非常不相關)，則跳過此結果
                if match_score < 0.12:
                    continue

            # Category-Aware 權重應用
            if enable_category_weight and target_categories:
                category_weight = calculate_category_weight(category, target_categories, boost_keywords)
                final_score = final_score * category_weight

            # 使用match_score作為額外的融合/提升因子：
            # 強匹配會進一步提升分數，弱匹配則維持或略降
            if enable_category_weight and target_categories:
                alpha = 0.45
                final_score = final_score * (1.0 + alpha * match_score)
            
            # 屬性級別匹配：檢查query中提及的特定屬性（如防水、降噪）是否在產品中出現
            # 這有助於在同category產品間進行更細粒度的排序
            attr_score = compute_attribute_match_score(metadata, query)
            if attr_score > 0.5:
                # 如果產品與query中提及的屬性較好匹配，進一步提升分數
                beta = 0.3
                final_score = final_score * (1.0 + beta * attr_score)
            
            # 產品類型匹配：檢查query中提及的特定產品型號（如喇叭vs耳機）是否在產品名稱中出現
            # 這在同category產品中提供最高優先級的排序信號
            type_score = compute_product_type_match_score(metadata, query)
            if type_score >= 1.0:
                # 產品名稱精確匹配query提及的產品類型 -> 強提升 (乘以1.5)
                final_score = final_score * 1.5
            elif type_score < 0.5:
                # 產品名稱不包含query提及的產品類型 -> 強降權 (乘以0.5)
                final_score = final_score * 0.5
            
            # 如果提供了增強關鍵詞，檢查內容中是否包含，並提升分數
            if boost_keywords:
                content_lower = (doc.page_content + product_name).lower()
                for keyword in boost_keywords:
                    if keyword.lower() in content_lower:
                        # 關鍵詞匹配時進一步提升
                        final_score = min(final_score * 1.15, 1.0)
            
            output.append({
                "product_name": product_name,
                "category": category,
                "price": price,
                "similarity_score": round(min(final_score, 1.0), 4),  # 確保不超過1.0
                "content": doc.page_content,
                "metadata": metadata
            })
            
            # 達到所需的結果數量後停止
            if len(output) >= limit:
                break
        
        # 按最終分數重新排序
        output.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # ========== 去重：保留每個product_id的最高分結果 ==========
        seen_product_ids = set()
        deduplicated_output = []
        for result in output:
            product_id = result['metadata'].get('product_id', '')
            if product_id and product_id not in seen_product_ids:
                deduplicated_output.append(result)
                seen_product_ids.add(product_id)
            elif not product_id:
                # 如果沒有product_id，仍然添加
                deduplicated_output.append(result)
        
        return deduplicated_output[:limit]
    except Exception as e:
        # 語義搜索失敗時回退到關鍵字搜索或返回空列表
        return []


def hybrid_search_products(
    vectorstore_updater,
    query: str,
    limit: int = 10,
    score_threshold: float = 0.2,
    product_only: bool = True,
    bm25_weight: float = 0.4,
    vector_weight: float = 0.6,
    enable_category_weight: bool = True
) -> List[Dict[str, Any]]:
    """
    混合搜索：結合BM25關鍵字搜索和向量相似度搜索
    提供更平衡的結果，特別是對keyword-rich查詢
    
    Args:
        vectorstore_updater: VectorstoreUpdater 實例
        query: 自然語言查詢字符串
        limit: 最多返回結果數
        score_threshold: 相似度分數閾值
        product_only: 如果為 True，只返回產品（過濾規則文檔）
        bm25_weight: BM25搜索的權重 (預設0.4)
        vector_weight: 向量搜索的權重 (預設0.6)
        enable_category_weight: 是否啟用category-aware權重
        
    Returns:
        融合BM25和向量搜索的產品結果
    """
    if vectorstore_updater is None:
        return []
    
    try:
        from langchain_community.retrievers import BM25Retriever
        vectorstore = vectorstore_updater.vectorstore
        
        # ========== 1. BM25關鍵字搜索 ==========
        # 從vectorstore獲取所有產品documents
        try:
            # 獲取所有documents用於BM25 index
            all_docs = vectorstore.get()  # 嘗試獲取所有documents
            if not all_docs or not all_docs.get('documents'):
                # 備用方案：使用empty query檢索所有文檔
                all_docs = []
                for doc, score in vectorstore.similarity_search_with_relevance_scores("", k=1000):
                    if doc not in all_docs:
                        all_docs.append(doc)
        except:
            # 如果無法獲取所有documents，使用向量搜索獲取初步候選
            all_docs = []
        
        # 創建BM25 retriever
        if all_docs:
            bm25_retriever = BM25Retriever.from_documents(all_docs)
            bm25_results_raw = bm25_retriever.invoke(query, k=limit*3)
            
            # 標準化BM25分數 (LangChain BM25不返回explicit scores，所以基於排名)
            bm25_scores = {}
            for i, doc in enumerate(bm25_results_raw):
                doc_id = id(doc) # 使用object id作為key
                bm25_scores[doc_id] = 1.0 - (i / (len(bm25_results_raw) + 1))  # 排名越靠前分數越高
        else:
            bm25_scores = {}
        
        # ========== 2. 向量相似度搜索 ==========
        # 推理目標categories以便於後續嚴格過濾
        target_categories = infer_target_categories_from_query(query) if enable_category_weight else []

        vector_results = semantic_search_products(
            vectorstore_updater,
            query,
            limit=limit*3,
            score_threshold=score_threshold,
            product_only=product_only,
            enable_category_weight=enable_category_weight
        )
        
        # ========== 3. 融合結果 ==========
        # 按product_id去重並融合分數
        merged_results = {}
        
        # 添加BM25結果
        for doc in bm25_results_raw[:limit*2]:
            metadata = getattr(doc, 'metadata', {}) or {}
            if product_only and metadata.get('source') != 'product_db':
                continue
            
            product_id = metadata.get('product_id', '')
            if not product_id:
                continue
            
            doc_id_key = id(doc)
            bm25_score = bm25_scores.get(doc_id_key, 0.0)
            
            if product_id not in merged_results:
                merged_results[product_id] = {
                    'product_name': metadata.get('product_name', ''),
                    'category': metadata.get('category', ''),
                    'price': metadata.get('price', ''),
                    'bm25_score': bm25_score,
                    'vector_score': 0.0,
                    'metadata': metadata
                }
            else:
                merged_results[product_id]['bm25_score'] = max(
                    merged_results[product_id]['bm25_score'], bm25_score
                )
        
        # 添加向量搜索結果
        for result in vector_results[:limit*2]:
            product_id = result['metadata'].get('product_id', '')
            if not product_id:
                continue
            
            vector_score = result['similarity_score']
            
            if product_id not in merged_results:
                merged_results[product_id] = {
                    'product_name': result['product_name'],
                    'category': result['category'],
                    'price': result['price'],
                    'bm25_score': 0.0,
                    'vector_score': vector_score,
                    'metadata': result['metadata']
                }
            else:
                merged_results[product_id]['vector_score'] = max(
                    merged_results[product_id]['vector_score'], vector_score
                )
        
        # ========== 4. 計算最終融合分數 ==========
        final_results = []
        for product_id, data in merged_results.items():
            # 標準化分數到 [0, 1]
            bm25_normalized = data['bm25_score']  # 已經在[0,1]
            vector_normalized = data['vector_score']  # 已經在[0,1]
            
            # 加權融合
            final_score = (bm25_normalized * bm25_weight) + (vector_normalized * vector_weight)

            # 計算category match score並用於過濾與提升
            match_score = 1.0
            if target_categories:
                # 先用寬鬆的布爾匹配過濾掉完全不相關的產品
                if not is_product_matching_categories(data.get('metadata', {}), target_categories):
                    continue

                match_score = compute_category_match_score(data.get('metadata', {}), target_categories)
                if match_score < 0.12:
                    # 非常不相關，跳過
                    continue

                # 使用match_score提升最終分數（避免單一商品硬編碼）
                alpha = 0.45
                final_score = final_score * (1.0 + alpha * match_score)

            # 屬性級別匹配：檢查query中提及的特定屬性
            attr_score = compute_attribute_match_score(data.get('metadata', {}), query)
            if attr_score > 0.5:
                beta = 0.3
                final_score = final_score * (1.0 + beta * attr_score)

            # 產品類型匹配：檢查產品名稱是否包含query中提及的產品型號
            type_score = compute_product_type_match_score(data.get('metadata', {}), query)
            if type_score >= 1.0:
                # 產品名稱精確匹配query提及的產品類型 -> 強提升 (乘以1.5)
                final_score = final_score * 1.5
            elif type_score < 0.5:
                # 產品名稱不包含query提及的產品類型 -> 強降權 (乘以0.5)
                final_score = final_score * 0.5

            # 確保至少其中一個搜索找到相關結果
            if final_score >= score_threshold:
                final_results.append({
                    'product_name': data['product_name'],
                    'category': data['category'],
                    'price': data['price'],
                    'similarity_score': round(final_score, 4),
                    'bm25_component': round(bm25_normalized, 4),
                    'vector_component': round(vector_normalized, 4),
                    'metadata': data['metadata']
                })
        
        # 按最終分數排序
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return final_results[:limit]
    
    except ImportError:
        # 如果BM25Retriever不可用，降級到純向量搜索
        return semantic_search_products(
            vectorstore_updater,
            query,
            limit=limit,
            score_threshold=score_threshold,
            product_only=product_only,
            enable_category_weight=enable_category_weight
        )
    except Exception as e:
        # 任何錯誤都降級到純向量搜索
        return semantic_search_products(
            vectorstore_updater,
            query,
            limit=limit,
            score_threshold=score_threshold,
            product_only=product_only,
            enable_category_weight=enable_category_weight
        )


def search_products(vectorstore_updater, keyword: str, limit: int = 10) -> List[dict]:
    """Thin wrapper for VectorstoreUpdater.search_products (keyword-based)"""
    if vectorstore_updater is None:
        return []
    try:
        return vectorstore_updater.search_products(keyword, limit=limit)
    except Exception:
        return []


def get_documents_from_retriever(retriever, query: str, k: int = 1):
    """
    尝试通过 retriever.invoke 或 retriever.get_relevant_documents 获取文档列表。
    返回一个文档对象列表（可能是 langchain Document），或空列表。
    """
    if retriever is None:
        return []
    try:
        # prefer invoke (used in existing code)
        docs = retriever.invoke(query)
        return docs or []
    except Exception:
        try:
            # fallback for other retriever implementations
            docs = retriever.get_relevant_documents(query)
            return docs or []
        except Exception:
            return []


def combine_documents_content(docs: List[object]) -> str:
    """Combine page_content from a list of document-like objects."""
    if not docs:
        return ""
    parts = []
    for d in docs:
        try:
            text = getattr(d, "page_content", None)
            if text is None and isinstance(d, dict):
                text = d.get("page_content") or d.get("content")
            if text:
                parts.append(text)
        except Exception:
            continue
    return "\n---\n".join(parts)
