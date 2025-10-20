"""
생성된 Summary 샘플 파일 검증 스크립트
"""

import json
import uuid
from pathlib import Path
from datetime import datetime


def validate_summary_samples():
    """50개 샘플 파일 검증"""

    samples_dir = Path(__file__).parent / "ocr_summaries"

    if not samples_dir.exists():
        print(f"❌ Directory not found: {samples_dir}")
        return False

    # 파일 목록 가져오기
    json_files = sorted(samples_dir.glob("sample_*.json"))
    print(f"📁 Found {len(json_files)} JSON files\n")

    if len(json_files) != 50:
        print(f"❌ Expected 50 files, but found {len(json_files)}")
        return False

    print("✅ File count: 50\n")

    # 각 파일 검증
    errors = []
    project_ids = set()
    file_ids = set()
    summary_ids = set()

    for i, file_path in enumerate(json_files, start=1):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 필수 필드 확인
            required_fields = ["summary_id", "project_id", "file_id", "summary_text", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                errors.append(f"{file_path.name}: Missing fields {missing_fields}")
                continue

            # UUID 검증
            try:
                uuid.UUID(data["summary_id"])
                summary_ids.add(data["summary_id"])
            except (ValueError, AttributeError):
                errors.append(f"{file_path.name}: Invalid UUID - {data['summary_id']}")

            # project_id 검증
            project_ids.add(data["project_id"])

            # file_id 검증
            file_ids.add(data["file_id"])

            # created_at 검증 (ISO 8601 형식)
            try:
                datetime.fromisoformat(data["created_at"].replace("+00:00", ""))
            except (ValueError, AttributeError):
                errors.append(f"{file_path.name}: Invalid timestamp - {data['created_at']}")

            # summary_text 길이 확인
            text_length = len(data["summary_text"])
            if text_length == 0:
                errors.append(f"{file_path.name}: Empty summary_text")
            elif text_length > 500:
                print(f"⚠️  {file_path.name}: summary_text length {text_length} chars (>500)")

        except json.JSONDecodeError as e:
            errors.append(f"{file_path.name}: Invalid JSON - {e}")
        except Exception as e:
            errors.append(f"{file_path.name}: Unexpected error - {e}")

    # 전체 검증 결과
    print("="*60)
    print("📊 Validation Results\n")

    # project_id 검증
    if len(project_ids) == 1 and 1001 in project_ids:
        print("✅ All project_ids are 1001")
    else:
        print(f"❌ project_ids are not consistent: {project_ids}")
        errors.append(f"project_ids should all be 1001, but found: {project_ids}")

    # file_id 검증
    expected_file_ids = set(range(1, 51))
    if file_ids == expected_file_ids:
        print("✅ All file_ids are 1-50 (sequential)")
    else:
        missing_ids = expected_file_ids - file_ids
        extra_ids = file_ids - expected_file_ids
        if missing_ids:
            print(f"❌ Missing file_ids: {sorted(missing_ids)}")
            errors.append(f"Missing file_ids: {sorted(missing_ids)}")
        if extra_ids:
            print(f"❌ Extra file_ids: {sorted(extra_ids)}")
            errors.append(f"Extra file_ids: {sorted(extra_ids)}")

    # summary_id 중복 검증
    if len(summary_ids) == len(json_files):
        print("✅ All summary_ids are unique")
    else:
        print(f"❌ Duplicate summary_ids detected")
        errors.append(f"Expected {len(json_files)} unique UUIDs, but got {len(summary_ids)}")

    # 오류 출력
    if errors:
        print("\n❌ Validation Errors:\n")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("\n✅ All validations passed!")
        print(f"✅ Total samples: {len(json_files)}")
        print(f"✅ All UUIDs valid and unique")
        print(f"✅ All schemas correct")
        return True


if __name__ == "__main__":
    success = validate_summary_samples()
    exit(0 if success else 1)
