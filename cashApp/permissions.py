# cashApp/permissions.py
"""
The single place that decides who may do what on a project.

Before this module the rules lived separately in project_list, project_detail,
transaction_create, dynamic_entry_create ... and disagreed with each other.
Every view now asks these helpers instead.

Role of a user on a project (highest match wins):

    ADMIN        user_type == 'admin'                         full access, every project
    OWNER        project.user                                 manage project + members, add entries
    CONTRIBUTOR  ProjectPermission 'edit'                     view + add transactions / rows
                 or member with no permission row
    VIEWER       ProjectPermission 'view'                     read only
    NONE         ProjectPermission 'hide', or no relation     no access

Notes
  * An explicit 'hide' always beats plain membership, but never beats ownership.
  * A 'view'/'edit' row grants access even if the user is not in project.members.
  * Frozen / inactive users have no role anywhere (defence in depth: the
    FrozenUserMiddleware already logs them out).
  * No database change is needed: this only reads Project.user, Project.members
    and ProjectPermission.
"""
from enum import IntEnum

from django.db.models import Q

from .models import Project, ProjectPermission


class Role(IntEnum):
    NONE        = 0
    VIEWER      = 1
    CONTRIBUTOR = 2
    OWNER       = 3
    ADMIN       = 4


def _usable(user):
    """Authenticated, active and not frozen."""
    return bool(
        user is not None
        and user.is_authenticated
        and user.is_active
        and not getattr(user, 'is_frozen', False)
    )


# ── Role lookup ────────────────────────────────────────────────────────────────

def get_project_role(user, project):
    if project is None or not _usable(user):
        return Role.NONE
    if user.is_admin:
        return Role.ADMIN
    if project.user_id == user.id:
        return Role.OWNER

    level = (
        ProjectPermission.objects
        .filter(project=project, user=user)
        .values_list('access_level', flat=True)
        .first()
    )
    if level == 'hide':
        return Role.NONE
    if level == 'edit':
        return Role.CONTRIBUTOR
    if level == 'view':
        return Role.VIEWER
    if project.members.filter(pk=user.pk).exists():
        return Role.CONTRIBUTOR
    return Role.NONE


def visible_projects(user):
    """Projects the user may at least view. Same rules as get_project_role, as a queryset."""
    if not _usable(user):
        return Project.objects.none()
    if user.is_admin:
        return Project.objects.all()

    perms   = ProjectPermission.objects.filter(user=user)
    hidden  = perms.filter(access_level='hide').values('project_id')
    granted = perms.filter(access_level__in=('view', 'edit')).values('project_id')

    return Project.objects.filter(
        Q(user=user) | ((Q(members=user) | Q(pk__in=granted)) & ~Q(pk__in=hidden))
    ).distinct()


# ── Capabilities ───────────────────────────────────────────────────────────────

def can_view_project(user, project):
    return get_project_role(user, project) >= Role.VIEWER


def can_add_entries(user, project):
    """Add transactions or dynamic rows."""
    return get_project_role(user, project) >= Role.CONTRIBUTOR


def can_manage_project(user, project):
    """Edit the project, manage its members."""
    return get_project_role(user, project) >= Role.OWNER


def can_delete_project(user, project):
    """
    Admins may delete any project. An owner may only delete a project that holds
    no financial data - deleting one with transactions would erase records and
    bypass the admin-approved delete workflow. (Step 4 replaces this with soft delete.)
    """
    role = get_project_role(user, project)
    if role == Role.ADMIN:
        return True
    if role == Role.OWNER:
        return not (project.transactions.exists() or project.dynamic_rows.exists())
    return False


def can_edit_transaction(user, transaction):
    """Edit it, or request its deletion."""
    if not _usable(user) or transaction.is_deleted:
        return False
    if user.is_admin:
        return True
    if transaction.user_id != user.id or transaction.delete_requested:
        return False
    if transaction.project_id is None:           # legacy entry without a project
        return True
    return get_project_role(user, transaction.project) >= Role.CONTRIBUTOR


def editable_transaction_ids(user, role, transactions):
    """
    Ids (from the given queryset) the user may edit/delete, so a template can show
    the buttons only where they will actually work.
    """
    if role == Role.ADMIN:
        return set(transactions.values_list('pk', flat=True))
    if role >= Role.CONTRIBUTOR:
        return set(
            transactions.filter(user=user, delete_requested=False)
            .values_list('pk', flat=True)
        )
    return set()