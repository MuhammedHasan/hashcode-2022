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
        if self.skills[role.skill] <= role.level:
            self.skills[role.skill] += 1

    def valid_role(self, project, role, members, current_day):
        if role.skill not in self.skills:
            return False

        if self.skills[role.skill] >= role.level:
            if current_day >= self.busy_until:
                return True

        for _, mentor in members.items():
            if mentor.name != self.name:
                if role.skill in mentor.skills:
                    if mentor.skills[role.skill] >= role.level:
                        if self.skills[role.skill] >= role.level - 1:
                            if current_day >= self.busy_until:
                                return True

        return False

    def assign(self, project, role, project_start_day):
        self.busy_until = project_start_day + project.num_days
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

    def gain(self, day):
        day_diff = day - self.best_before

        if day_diff <= 0:
            return self.score

        return self.score - day_diff

    def fill_roles(self, skill_contributor, current_day):
        members = dict()  # key role_id value cont

        assigned_member = set()

        for role_id, role in sorted(enumerate(self.roles), key=lambda x: -x[1][1]):
            conts = skill_contributor[role.skill]

            conts = sorted([
                (level, cont)
                for level, cont in conts
                if level >= role.level
            ], key=lambda x: (x[1].busy_until, x[0]))

            match = False
            for _, cont in conts:
                if cont.name in assigned_member:
                    continue

                if cont.valid_role(self, role, members, current_day):
                    members[role_id] = cont
                    assigned_member.add(cont.name)
                    match = True
                    break

            if not match:
                return []  # no member

        return [
            (members[role_id], role)
            for role_id, role in enumerate(self.roles)
        ]

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
        skill_contributor[skill] = sorted(conts, key=lambda x: -x[0])

    projects = sorted(projects, key=lambda p: (
        p.start_day, -(p.score / p.num_days)))

    output = dict()

    unassigned_projects = list()

    for project in tqdm(projects):
        conts_roles = project.fill_roles(skill_contributor)

        if len(conts_roles) == 0:
            # unassigned_projects.append(project)
            continue

        for cont, role in conts_roles:
            cont.assign(project, role, conts_roles.copy())

        output[project.name] = [cont for cont, _ in conts_roles]

        # for un_project in unassigned_projects:
        #     conts_roles = un_project.fill_roles(skill_contributor)

        #     if len(conts_roles) == 0:
        #         next

        #     for cont, role in conts_roles:
        #         cont.assign(un_project, role)
        #     output[un_project.name] = [cont for cont, _ in conts_roles]

    return output


def solve_day(contributors, projects):
    # insan kaynaklari
    skill_contributor = defaultdict(list)

    for cont in contributors:
        for skill, skill_level in cont.skills.items():
            skill_contributor[skill].append((skill_level, cont))

    skill_contributor = dict(skill_contributor)

    for skill, conts in skill_contributor.items():
        skill_contributor[skill] = sorted(conts, key=lambda x: -x[0])

    # projects = sorted(projects, key=lambda p: (
    #     p.start_day, -(p.score / p.num_days)))

    output = dict()

    day = 0

    assigned_projects = set()

    num_projects = len(projects)

    while len(projects) > 0:

        print(max([
            cont.busy_until
            for cont in contributors
        ]))

        gains = [
            (project.gain(day), project)
            for project in projects
        ]
        # print([i for i, j in gains])

        projects = [
            project
            for gain, project in gains
            if (gain > 0) and (project.name not in assigned_projects)
        ]

        gains = sorted(gains, key=lambda x: -
                       (x[0] / (x[1].num_days * len(x[1].roles))))

        for _, project in gains:
            conts_roles = project.fill_roles(skill_contributor, day)

            if len(conts_roles) == 0:
                continue

            project_start_day = max(
                [cont.busy_until for cont, _ in conts_roles])

            for cont, role in conts_roles:
                cont.assign(project, role, project_start_day)

            assigned_projects.add(project.name)
            output[project.name] = [cont for cont, _ in conts_roles]
            break

        day += 1
        print(f'{day}/{len(projects)}/{num_projects}/{len(conts_roles)}')

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
        # 'a_an_example.in.txt',
        # 'b_better_start_small.in.txt',
        # 'c_collaboration.in.txt',
        'd_dense_schedule.in.txt',
        # 'e_exceptional_skills.in.txt',
        # 'f_find_great_mentors.in.txt'
    ]

    for i in files:
        contributors, projects = read('../input/' + i)

        # print([
        #     i.num_days
        #     for i in projects
        # ])
        # print(len(projects))

        solution = solve_day(contributors, projects)
        # # solution = solve(contributors, projects)
        write('../output/' + i, solution)


if __name__ == "__main__":
    main()
