from tqdm import tqdm
from collections import namedtuple, defaultdict


class Contributor:

    def __init__(self, name, skills=None):
        self.name = name
        self.skills = skills or dict()
        self.busy_until = 0

    def add_skill(self, name, level):
        self.skills[name] = level

    def level_up(self, role):
        # if mentoring, then can be small by one
        if self.skills[role.skill] == role.level:
            self.skills[role.skill] += 1

    def valid_role(self, project, role):
        if role.skill not in self.skills:
            return False

        if self.skills[role.skill] >= role.level:
            if project.start_day >= self.busy_until:
                return True

        return False

    def assign(self, project, role):
        # TO FIX: if not assigning on start day
        self.busy_until = project.best_before
        self.level_up(role)

    def __str__(self):
        return f'Contributor({self.name})'


class Project:

    def __init__(self, name, num_days, score, best_before, roles=None):
        self.name = name
        self.num_days = num_days
        self.score = score
        self.best_before = best_before
        self.roles = roles or list()

    def add_role(self, role):
        self.roles.append(role)

    @property
    def start_day(self):
        return self.best_before - self.num_days

    def fill_roles(self, skill_contributor):
        members = list()

        assigned_member = set()

        for role in self.roles:
            conts = skill_contributor[role.skill]

            match = False
            for _level, cont in conts:
                if cont.name in assigned_member:
                    continue

                if cont.valid_role(self, role):
                    members.append((cont, role))
                    assigned_member.add(cont.name)
                    match = True
                    break

            if not match:
                return []  # no member

        return members

    def __str__(self):
        return f'Project({self.name})'


Role = namedtuple('Role', ['skill', 'level'])


def read(path):
    contributors = list()
    projects = list()

    with open(path) as f:
        num_contributors, num_projects = map(int, next(f).strip().split())

        for _ in range(num_contributors):
            name, num_skills = next(f).strip().split()
            num_skills = int(num_skills)

            cont = Contributor(name)

            for _ in range(num_skills):
                skill_name, skill_level = next(f).strip().split()
                cont.add_skill(skill_name, int(skill_level))

            contributors.append(cont)

        for _ in range(num_projects):
            project_name, num_days, score, best_before, num_roles = next(
                f).strip().split()

            num_days = int(num_days)
            score = int(score)
            num_roles = int(num_roles)
            best_before = int(best_before)

            project = Project(project_name, num_days, score, best_before)

            for _ in range(num_roles):
                skill, level = next(f).strip().split()
                level = int(level)
                role = Role(skill, level)
                project.add_role(role)

            projects.append(project)

    return contributors, projects


def solve(contributors, projects):

    # insan kaynaklari
    skill_contributor = defaultdict(list)

    for cont in contributors:
        for skill, skill_level in cont.skills.items():
            skill_contributor[skill].append((skill_level, cont))

    skill_contributor = dict(skill_contributor)

    for skill, conts in skill_contributor.items():
        skill_contributor[skill] = sorted(conts, key=lambda x: x[0])

    projects = sorted(projects, key=lambda p: (
        p.start_day, -(p.score / p.num_days)))

    output = dict()

    unassigned_projects = list()

    for project in tqdm(projects):
        conts_roles = project.fill_roles(skill_contributor)

        if len(conts_roles) == 0:
            # unassigned_projects.append(project)
            next

        for cont, role in conts_roles:
            cont.assign(project, role)

        output[project.name] = [cont for cont, _ in conts_roles]

        # for un_project in unassigned_projects:
        #     conts_roles = un_project.fill_roles(skill_contributor)

        #     if len(conts) == 0:
        #         next

        #     for cont, role in conts_roles:
        #         cont.assign(project, role)
        #     output[project.name] = [cont for cont, _ in conts_roles]

    return output


def write(path, solution):

    with open(path, 'w') as f:
        num_projects = sum(
            len(conts) > 0
            for _, conts in solution.items()
        )
        f.write(str(num_projects) + '\n')

        for project_name, conts in solution.items():
            if len(conts):
                f.write(project_name + '\n')
                f.write(
                    ' '.join(i.name for i in conts) + '\n'
                )


def main():
    files = [
        'a_an_example.in.txt',
        'b_better_start_small.in.txt',
        'c_collaboration.in.txt',
        'd_dense_schedule.in.txt',
        'e_exceptional_skills.in.txt',
        'f_find_great_mentors.in.txt'
    ]

    for i in files:
        contributors, projects = read('../input/' + i)
        solution = solve(contributors, projects)
        write('../output/' + i, solution)


if __name__ == "__main__":
    main()
