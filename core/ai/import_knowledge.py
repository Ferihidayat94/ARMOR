import os

from core.models import KnowledgeDocument

BASE_PATH = "/var/www/armor/media/knowledge"

for root, dirs, files in os.walk(BASE_PATH):

    for file_name in files:

        if file_name.lower().endswith(".pdf"):

            full_path = os.path.join(root, file_name)

            relative_path = os.path.relpath(
                full_path,
                "/var/www/armor/media"
            )

            title = file_name.replace(".pdf", "")

            category = "MANUAL"

            lower_root = root.lower()

            if "sop" in lower_root:
                category = "SOP"

            elif "history" in lower_root:
                category = "HISTORY"

            exists = KnowledgeDocument.objects.filter(
                title=title
            ).exists()

            if not exists:

                KnowledgeDocument.objects.create(
                    title=title,
                    category=category,
                    file=relative_path
                )

                print("IMPORTED:", file_name)

print("SELESAI IMPORT")
