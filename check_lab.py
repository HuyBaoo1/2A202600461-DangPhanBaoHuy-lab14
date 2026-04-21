import json
import os
import sys

def validate_lab():
    print("🔍 Đang kiểm tra định dạng bài nộp...")
    print("=" * 60)

    required_files = [
        "reports/summary.json",
        "reports/benchmark_results.json",
        "analysis/failure_analysis.md"
    ]

    errors = []
    warnings = []

    # ========== 1. Kiểm tra sự tồn tại của tất cả file ==========
    print("\n📋 Kiểm tra file bắt buộc:")
    missing = []
    for f in required_files:
        if os.path.exists(f):
            print(f"   ✅ {f}")
        else:
            print(f"   ❌ {f}")
            missing.append(f)
            errors.append(f"Thiếu file bắt buộc: {f}")

    if missing:
        print(f"\n❌ FATAL: Thiếu {len(missing)} file. Hãy chạy 'python main.py' trước.")
        return False

    # ========== 2. Kiểm tra nội dung summary.json ==========
    print("\n📊 Kiểm tra reports/summary.json:")
    try:
        with open("reports/summary.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON không hợp lệ: {e}")
        errors.append(f"summary.json parse error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        errors.append(f"summary.json read error: {e}")
        return False

    # ========== 3. Kiểm tra required fields ==========
    required_fields = {
        "v1": ["metadata", "metrics"],
        "v2": ["metadata", "metrics"],
        "regression": ["decision", "reasoning", "deltas"],
        "failure_analysis": ["total_failures", "clusters"]
    }

    print("   Checking structure:")
    for section, fields in required_fields.items():
        if section not in data:
            print(f"   ❌ Thiếu section: {section}")
            errors.append(f"Thiếu section: {section}")
            continue
        
        for field in fields:
            if field in data[section]:
                print(f"   ✅ {section}.{field}")
            else:
                print(f"   ⚠️ {section}.{field} (missing)")
                warnings.append(f"Thiếu field {section}.{field}")

    # ========== 4. Expert Checks - Retrieval Metrics ==========
    print("\n🔬 Expert Checks:")
    
    v2_metrics = data.get("v2", {}).get("metrics", {})
    
    has_hit_rate = "hit_rate" in v2_metrics
    has_mrr = "avg_mrr" in v2_metrics
    has_retrieval = has_hit_rate and has_mrr
    
    if has_retrieval:
        hit_rate = v2_metrics["hit_rate"]
        mrr = v2_metrics["avg_mrr"]
        print(f"   ✅ Retrieval Metrics Found:")
        print(f"      - Hit Rate: {hit_rate*100:.1f}% (target: ≥ 80%)")
        print(f"      - MRR: {mrr:.3f} (target: ≥ 0.70)")
        
        if hit_rate < 0.8:
            warnings.append(f"Hit Rate quá thấp: {hit_rate*100:.1f}% < 80%")
        if mrr < 0.70:
            warnings.append(f"MRR quá thấp: {mrr:.3f} < 0.70")
    else:
        print(f"   ❌ CRITICAL: Thiếu Retrieval Metrics (hit_rate, avg_mrr)")
        errors.append("Thiếu Retrieval Metrics")

    # ========== 5. Multi-Judge Consensus Check ==========
    has_agreement = "agreement_rate" in v2_metrics
    if has_agreement:
        agreement_rate = v2_metrics["agreement_rate"]
        print(f"   ✅ Multi-Judge Metrics Found:")
        print(f"      - Agreement Rate: {agreement_rate*100:.1f}% (target: ≥ 75%)")
        if agreement_rate < 0.75:
            warnings.append(f"Agreement Rate quá thấp: {agreement_rate*100:.1f}% < 75%")
    else:
        print(f"   ⚠️ Thiếu Multi-Judge Metrics (agreement_rate)")
        warnings.append("Thiếu agreement_rate")

    # ========== 6. Regression Testing Check ==========
    regression = data.get("regression", {})
    decision = regression.get("decision")
    
    if decision:
        print(f"   ✅ Regression Testing Found:")
        print(f"      - Decision: {decision}")
        deltas = regression.get("deltas", {})
        print(f"      - Score Delta: {deltas.get('score_delta', 'N/A'):+.3f}")
        print(f"      - Hit Rate Delta: {deltas.get('hitrate_delta', 'N/A'):+.3f}")
    else:
        print(f"   ❌ CRITICAL: Thiếu Regression Testing")
        errors.append("Thiếu Regression Testing Decision")

    # ========== 7. Failure Analysis Check ==========
    print("\n📝 Kiểm tra failure_analysis.md:")
    
    with open("analysis/failure_analysis.md", "r", encoding="utf-8") as f:
        md_content = f.read()
    
    required_sections = [
        "5 Whys",
        "Root Cause",
        "Action Plan",
        "Failure Clustering"
    ]
    
    found_sections = 0
    for section in required_sections:
        if section in md_content:
            print(f"   ✅ Section: {section}")
            found_sections += 1
        else:
            print(f"   ❌ Section: {section} (not found)")
            warnings.append(f"failure_analysis.md missing: {section}")
    
    # ========== 8. Final Summary ==========
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    v2_meta = data.get("v2", {}).get("metadata", {})
    total_cases = v2_meta.get("total")
    
    if total_cases:
        print(f"✅ Total Test Cases: {total_cases}")
    
    if errors:
        print(f"\n❌ CRITICAL ERRORS ({len(errors)}):")
        for err in errors:
            print(f"   - {err}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"   - {warn}")
    
    if not errors:
        print(f"\n✅ PASSED: Bài lab đã sẵn sàng để chấm điểm!")
        return True
    else:
        print(f"\n❌ FAILED: Hãy fix các critical errors trên.")
        return False

if __name__ == "__main__":
    success = validate_lab()
    sys.exit(0 if success else 1)
