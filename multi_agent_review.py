"""
Multi-Agent Debate System for Self-Review and Improvement
通過多智能體辯論進行自我審視和改進
"""

import json
from typing import Dict, List, Tuple

class SearchQualityAnalyst:
    """搜索品質分析專家 - 聚焦於量化指標和性能問題"""
    
    def analyze(self) -> Dict:
        return {
            "role": "搜索品質分析專家",
            "current_status": {
                "success_rate": "60% (6/10 queries)",
                "average_similarity_score": "52.30%",
                "finding_any_result": "100% (全部找到至少1個結果)",
            },
            "critical_issues": [
                {
                    "issue": "4個查詢完全失敗 (queries 1,4,5,8)",
                    "impact": "40% 失敗率太高",
                    "affected_categories": ["音頻設備", "家務自動化", "便攜存儲", "家庭娛樂"],
                    "severity": "CRITICAL"
                },
                {
                    "issue": "電競椅超配 (overfitting)",
                    "symptom": "在4個不相關查詢中排名第1/2",
                    "products": ["Robot (51.70%)", "SSD (56.17%)", "Projector (48.01%)", "Speaker (45.36%)"],
                    "severity": "HIGH"
                },
                {
                    "issue": "短描述產品表現差",
                    "products": ["掃地機器人", "投影機", "SSD"],
                    "reason": "描述過短，語義信息不足",
                    "severity": "HIGH"
                }
            ],
            "bottleneck_analysis": {
                "vectorstore_quality": "Only 27 documents (25 products + 2 rules)",
                "product_description_length": "平均100-200字，不足以覆蓋多個use cases",
                "feature_tags_coverage": "15個tags，但缺乏層級化結構",
                "keyword_boosting": "只提升20%，不足以扭轉排序"
            }
        }

class SemanticArchitectureDesigner:
    """語義架構設計師 - 聚焦於系統架構改進"""
    
    def propose_improvements(self) -> Dict:
        return {
            "role": "語義架構設計師",
            "proposed_changes": [
                {
                    "priority": 1,
                    "change": "擴展產品內容和向量化",
                    "current": "每個產品1個document，平均150字",
                    "proposed": "每個產品3-5個document (名稱、特性、use cases、技術規格)",
                    "benefit": "語義密度提高3-5倍，相似度分離度提高",
                    "implementation": [
                        "為每個產品創建多個content chunks",
                        "每個chunk聚焦於不同維度 (features, use_cases, specs)",
                        "增加metadata區分chunk類型"
                    ],
                    "estimated_impact": "向量庫從27→80-100 documents，可望提升相似度精準度"
                },
                {
                    "priority": 2,
                    "change": "實現分類感知搜索 (category-aware search)",
                    "current": "純向量相似度，無category權重",
                    "proposed": "根據query隱含的category，加權該category產品",
                    "benefit": "防止無關產品overfitting",
                    "implementation": [
                        "建立query→category映射表",
                        "提取query中的category keywords (e.g., '喇叭'→'音頻設備')",
                        "對同category產品加乘權重 (×1.5-2.0)",
                        "對不同category產品減乘權重 (×0.5-0.8)"
                    ],
                    "estimated_impact": "電競椅在不相關queries中的排名下降，提升4個失敗query成功率"
                },
                {
                    "priority": 3,
                    "change": "混合搜索 (Hybrid: BM25 + Vector)",
                    "current": "純向量搜索",
                    "proposed": "BM25關鍵字搜索 (50%) + 向量搜索 (50%)",
                    "benefit": "對exact/partial keyword match有強相關性",
                    "implementation": [
                        "集成BM25檢索器 (langchain BM25Retriever)",
                        "並行執行keyword + semantic搜索",
                        "融合結果: (bm25_score × 0.5) + (vector_score × 0.5)",
                        "調整score_threshold適應混合評分"
                    ],
                    "estimated_impact": "特別提升'防水的藍牙喇叭'等keyword-rich queries"
                }
            ],
            "architectural_bottlenecks": {
                "current_approach": "Single-chunk per product, pure vector similarity",
                "limitation": "無法區分產品差異維度，generic descriptions overfitting",
                "solution": "Multi-chunk strategy + weighted category awareness + hybrid retrieval"
            }
        }

class ImplementationEngineer:
    """實現工程師 - 聚焦於可執行的具體步驟"""
    
    def generate_action_plan(self) -> Dict:
        return {
            "role": "實現工程師",
            "immediate_actions": [
                {
                    "step": 1,
                    "title": "擴展產品描述和創建多個chunks",
                    "tasks": [
                        "為每個產品增加3個維度的詳細描述：",
                        "  - Features & Specs: 技術參數、規格",
                        "  - Use Cases: 應用場景、用戶故事",
                        "  - Comparison: 與相似產品的對比優勢",
                        "修改create_vectorstore.py:",
                        "  - 為每個產品創建3-4個Document objects",
                        "  - 每個document含chunk_type metadata (features/usecases/specs)",
                        "  - 保留product_id以便合併結果時去重"
                    ],
                    "estimated_lines": "~150 lines of code",
                    "time_estimate": "30分鐘"
                },
                {
                    "step": 2,
                    "title": "實現category-aware search權重",
                    "tasks": [
                        "創建category_mapper.json:",
                        "  key: category_keyword (e.g., '喇叭', 'speaker', '音箱')",
                        "  value: product_categories it belongs to",
                        "修改search.py semantic_search_products():",
                        "  - 從query提取category keywords",
                        "  - 對每個結果計算category相關性分數",
                        "  - 調整最終分數: final_score = vector_score × category_weight",
                        "  - category_weight範圍: 0.5 (opposite) - 2.0 (same)"
                    ],
                    "estimated_lines": "~80 lines of code",
                    "time_estimate": "25分鐘"
                },
                {
                    "step": 3,
                    "title": "集成BM25混合搜索",
                    "tasks": [
                        "修改create_vectorstore.py:",
                        "  - 同時創建BM25Retriever from LangChain",
                        "  - 保存bm25_index到./bm25_index",
                        "修改search.py:",
                        "  - 並行調用vector search和bm25 search",
                        "  - 融合分數: (bm25_normalized × 0.4) + (vector_normalized × 0.6)",
                        "  - 測試調整權重比例"
                    ],
                    "estimated_lines": "~100 lines of code",
                    "time_estimate": "35分鐘"
                },
                {
                    "step": 4,
                    "title": "更新create_vectorstore.py中的產品描述",
                    "tasks": [
                        "為merged_products.json中的每個產品增加3倍內容:",
                        "  - 掃地機器人: 清潔場景、導航方式、維護要點",
                        "  - 投影機: 顯示技術、應用場景、連接方式",
                        "  - SSD: 性能參數、用途、相容性",
                        "  - 藍牙喇叭: 防水等級、使用場景、音質特性",
                        "OR: 在create_vectorstore.py中動態生成use case chunks"
                    ],
                    "estimated_lines": "~200-300 characters per product",
                    "time_estimate": "40分鐘"
                },
                {
                    "step": 5,
                    "title": "重建向量庫並測試",
                    "tasks": [
                        "執行改進的create_vectorstore.py",
                        "驗證document計數 (27 → 80-100)",
                        "執行test_comprehensive.py",
                        "記錄新的成功率和相似度分數"
                    ],
                    "time_estimate": "15分鐘"
                }
            ],
            "total_implementation_time": "~145 分鐘 (~2.5小時)",
            "expected_success_rate_improvement": "60% → 85-90%",
            "key_metrics_to_track": [
                "Success rate (target: 90%)",
                "Average similarity score (target: 60%+)",
                "Failed query count (target: ≤1)",
                "Top-1 accuracy (target: 70%+)"
            ]
        }

class CriticalQuestioner:
    """批判性審問者 - 聚焦於識別假設和風險"""
    
    def challenge_assumptions(self) -> Dict:
        return {
            "role": "批判性審問者",
            "questions_and_risks": [
                {
                    "question": "多chunks真的會改善結果嗎？",
                    "risk": "可能增加noise，導致off-topic chunks被檢索",
                    "mitigation": [
                        "為每個chunk添加clear chunk_type metadata",
                        "使用metadata_filter降低noise chunks被檢索的概率",
                        "測試chunks創建前後的相似度分布"
                    ]
                },
                {
                    "question": "Category權重怎樣避免hardcoding失敗？",
                    "risk": "手動category mapping容易遺漏或錯誤",
                    "mitigation": [
                        "從merged_products.json自動提取category",
                        "使用LLM進行query→category推理，而非regex",
                        "允許多個category匹配(一個query可能涉及多個category)"
                    ]
                },
                {
                    "question": "BM25權重0.4/0.6是否最優？",
                    "risk": "固定權重可能不適應所有query類型",
                    "mitigation": [
                        "進行hyperparameter tuning",
                        "根據query特性動態調整 (keyword-rich → BM25高; semantic-rich → vector高)",
                        "在validation set上交叉驗證"
                    ]
                },
                {
                    "question": "會不會過度優化10個test queries？",
                    "risk": "Overfitting to test set，實際性能未必提升",
                    "mitigation": [
                        "創建additional 10-20個diverse test queries",
                        "分離training/test set",
                        "進行cross-validation"
                    ]
                }
            ],
            "success_criteria": {
                "must_have": [
                    "90% success rate on all 10 original test queries",
                    "≥1個失敗query改善到top-1或top-2",
                    "沒有回歸 (original successful queries仍成功)"
                ],
                "nice_to_have": [
                    "平均相似度提升到60%+",
                    "新增test queries成功率≥85%",
                    "響應時間不超過當前2倍"
                ]
            }
        }

class DebateOrchestrator:
    """辯論主持人 - 統合各角色意見"""
    
    def synthesize_debate(self) -> Dict:
        analyst = SearchQualityAnalyst()
        architect = SemanticArchitectureDesigner()
        engineer = ImplementationEngineer()
        questioner = CriticalQuestioner()
        
        return {
            "debate_summary": "Multi-Agent Analysis for 90% Success Rate Target",
            "key_findings": [
                "根本原因：產品描述不足 + 無category意識 + 純向量搜索 → 導致generic products overfitting",
                "解決方案等級：",
                "  L1 (必需): 多chunk策略 + category-aware權重",
                "  L2 (強烈推薦): 混合搜索 (BM25 + Vector)",
                "  L3 (可選): LLM-based category inference",
            ],
            "roles_analysis": {
                "品質分析專家": analyst.analyze(),
                "架構設計師": architect.propose_improvements(),
                "實現工程師": engineer.generate_action_plan(),
                "批判性審問者": questioner.challenge_assumptions()
            },
            "consensus_roadmap": [
                {
                    "phase": "Phase 1: Content Expansion",
                    "duration": "40分鐘",
                    "goal": "50%→65% success rate",
                    "actions": [
                        "擴展merged_products.json產品描述",
                        "創建multi-chunk architecture",
                        "重建向量庫 (27→80 documents)"
                    ]
                },
                {
                    "phase": "Phase 2: Category-Aware Search",
                    "duration": "30分鐘",
                    "goal": "65%→80% success rate",
                    "actions": [
                        "實現category keyword extraction",
                        "添加category weight機制",
                        "測試和調整權重參數"
                    ]
                },
                {
                    "phase": "Phase 3: Hybrid Search Integration",
                    "duration": "40分鐘",
                    "goal": "80%→90% success rate",
                    "actions": [
                        "集成BM25 retriever",
                        "實現score融合邏輯",
                        "進行hyperparameter tuning",
                        "最終驗證測試"
                    ]
                }
            ],
            "expected_outcomes": {
                "success_rate": "60% → 90%",
                "time_investment": "~2.5小時",
                "implementation_complexity": "Medium (150-200 lines新增代碼)",
                "risk_level": "Low (可逐步驗證，無破壞性改動)"
            }
        }

if __name__ == "__main__":
    orchestrator = DebateOrchestrator()
    debate_report = orchestrator.synthesize_debate()
    
    print("=" * 80)
    print("🤖 MULTI-AGENT DEBATE REPORT - 90% SUCCESS RATE ANALYSIS")
    print("=" * 80)
    print()
    
    print("📊 KEY FINDINGS:")
    for finding in debate_report["key_findings"]:
        print(f"  • {finding}")
    print()
    
    print("🎯 CONSENSUS ROADMAP:")
    for phase in debate_report["consensus_roadmap"]:
        print(f"\n{phase['phase']} ({phase['duration']})")
        print(f"  Goal: {phase['goal']}")
        for action in phase['actions']:
            print(f"    ✓ {action}")
    print()
    
    print("📈 EXPECTED OUTCOMES:")
    for key, value in debate_report["expected_outcomes"].items():
        print(f"  {key}: {value}")
    print()
    
    print("=" * 80)
    print("💡 DETAILED ANALYSIS SAVED TO: multi_agent_review_detailed.json")
    print("=" * 80)
    
    # Save detailed report
    with open("multi_agent_review_detailed.json", "w", encoding="utf-8") as f:
        json.dump(debate_report["roles_analysis"], f, ensure_ascii=False, indent=2)
