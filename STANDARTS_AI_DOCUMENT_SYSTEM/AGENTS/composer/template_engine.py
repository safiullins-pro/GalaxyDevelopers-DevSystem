import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    Движок для загрузки и рендеринга шаблонов с использованием Jinja2.
    """
    def __init__(self, template_dir: str = "/Volumes/Z7S/development/ALBERT_TOOLS_PLACE/DocumentsSystem/03_TEMPLATES"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.info(f"TemplateEngine initialized with template directory: {self.template_dir}")

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Рендерит шаблон с заданным контекстом.
        
        Args:
            template_path (str): Путь к файлу шаблона относительно template_dir.
            context (Dict[str, Any]): Словарь данных для заполнения шаблона.
            
        Returns:
            str: Отформатированный контент.
        """
        try:
            template = self.env.get_template(template_path)
            rendered_content = template.render(context)
            logger.info(f"Successfully rendered template: {template_path}")
            return rendered_content
        except Exception as e:
            logger.error(f"Error rendering template {template_path}: {e}")
            raise

# Пример использования (для тестирования)
async def main():
    engine = TemplateEngine()
    
    # Создадим временный шаблон для теста
    test_template_path = engine.template_dir / "test_doc.md"
    test_template_path.write_text("# {{ title }}\n\nAuthor: {{ author }}\n\n{{ content }}")

    context = {
        "title": "My Test Document",
        "author": "Chepuha",
        "content": "This is some test content for the document."
    }
    
    try:
        rendered = engine.render_template("test_doc.md", context)
        print("\n--- Rendered Content ---")
        print(rendered)
    except Exception as e:
        print(f"Failed to render template: {e}")
    finally:
        # Удалим временный шаблон
        if test_template_path.exists():
            test_template_path.unlink()

if __name__ == "__main__":
    asyncio.run(main())