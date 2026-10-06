from datetime import timedelta

from app import create_app
from database import db
from models import Category, Task, User
from utils.helpers import utcnow


def _user(name, email, password, role):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    return user


def seed_data():
    app = create_app()
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(db.delete(model))

        joao = _user('João Silva', 'joao@email.com', '1234', 'admin')
        maria = _user('Maria Santos', 'maria@email.com', 'abcd', 'user')
        pedro = _user('Pedro Oliveira', 'pedro@email.com', 'pass', 'manager')

        backend = Category(name='Backend', description='Tarefas de backend', color='#3498db')
        frontend = Category(name='Frontend', description='Tarefas de frontend', color='#2ecc71')
        devops = Category(name='DevOps', description='Tarefas de infraestrutura', color='#e74c3c')
        bug = Category(name='Bug', description='Correção de bugs', color='#e67e22')

        db.session.add_all([joao, maria, pedro, backend, frontend, devops, bug])
        db.session.flush()

        now = utcnow()
        tasks = [
            Task(title='Implementar autenticação JWT', description='Adicionar autenticação real com JWT', status='pending', priority=1, user_id=joao.id, category_id=backend.id, due_date=now - timedelta(days=3)),
            Task(title='Criar tela de login', description='Tela de login responsiva', status='in_progress', priority=2, user_id=maria.id, category_id=frontend.id, due_date=now + timedelta(days=5)),
            Task(title='Configurar CI/CD', description='Pipeline com GitHub Actions', status='done', priority=2, user_id=pedro.id, category_id=devops.id, tags='devops,ci,github'),
            Task(title='Corrigir bug no filtro de busca', description='Filtro não funciona com caracteres especiais', status='pending', priority=1, user_id=joao.id, category_id=bug.id, due_date=now - timedelta(days=1)),
            Task(title='Adicionar paginação na API', description='Endpoints retornam todos os registros', status='pending', priority=3, user_id=joao.id, category_id=backend.id, due_date=now + timedelta(days=10)),
            Task(title='Escrever testes unitários', description='Cobertura mínima de 80%', status='pending', priority=2, user_id=maria.id, category_id=backend.id),
            Task(title='Documentar API com Swagger', description='Gerar documentação automática', status='cancelled', priority=4, user_id=pedro.id, category_id=backend.id),
            Task(title='Refatorar models', description='Melhorar organização dos models', status='in_progress', priority=3, user_id=maria.id, category_id=backend.id, tags='refactor,tech-debt'),
            Task(title='Configurar monitoramento', description='Prometheus + Grafana', status='pending', priority=4, user_id=pedro.id, category_id=devops.id, due_date=now + timedelta(days=20)),
            Task(title='Melhorar validações de input', description='Usar marshmallow ou pydantic', status='pending', priority=3, user_id=joao.id, category_id=backend.id, tags='improvement,validation'),
        ]

        db.session.add_all(tasks)
        db.session.commit()

        def count(model):
            return db.session.scalar(db.select(db.func.count()).select_from(model))

        print("Seed concluído com sucesso!")
        print(f"  {count(User)} usuários")
        print(f"  {count(Category)} categorias")
        print(f"  {count(Task)} tasks")


if __name__ == '__main__':
    seed_data()
