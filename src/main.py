from tqdm import tqdm
from collections import namedtuple, defaultdict


class Contributor:

    def __init__(self, name):
        self.name = name
        self.skills = defaultdict(int)
        self.busy_until = 0

    def add_skill(self, name, level):
        self.skills[name] = level

    def level_up(self, role):
        if self.skills[role.skill] <= role.level:
            self.skills[role.skill] += 1

    def valid_role(self, role, mentor=None):
        level = self.skills[role.skill]

        if level >= role.level:
            return True

        if mentor is not None:
            if mentor.name == self.name:
                raise ValueError('One cannot mentor your self!')

            if mentor.valid_role(role):
                if level >= role.level - 1:
                    return True

        return False

    def valid_time(self, project_start_day):
        return project_start_day >= self.busy_until

    def assign(self, project, role, project_start_day):
        if not self.valid_time(project_start_day):
            raise ValueError('I am still busy cannot start on the project')

        self.busy_until = project_start_day + project.num_days
        self.level_up(role)

    def __repr__(self):
        return f'Contributor({self.name}, skills={self.skills}, busy_until={self.busy_until})'


Role = namedtuple('Role', ['skill', 'level'])


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

    def gain(self, project_start_day):
        late_days = min(0, project_start_day +
                        self.num_days - self.best_before)
        return self.score - late_days

    def cost(self):
        return self.num_days * len(self.roles)

    def __repr__(self):
        return f'Project({self.name}, num_days={self.num_days}, score={self.score}, best_before={self.best_before}, roles={self.roles})'


class HumanResources:

    def __init__(self, contributors):
        self.contributors = contributors
        # TODO: index for quick and link to contributor class

    def find_candidates(self, role):
        for cont in self.contributors:
            level = cont.skills[role.skill]

            if level >= role.level - 1:
                yield (level, cont)

    def fill_roles(self, project, start_day):
        members = dict()  # {role_id: cont}
        assigned_member = set()

        # sort by most important to least important skill
        roles = sorted(enumerate(project.roles),
                       key=lambda x: -x[1].level)

        for role_id, role in roles:
            candidates = self.find_candidates(role)

            # trade of busy vs skill
            candidates = sorted(candidates,
                                key=lambda x: (x[1].busy_until, x[0]))

            match = False

            for _, candidate in candidates:
                if candidate.name in assigned_member:
                    continue

                if candidate.valid_role(role) \
                   and candidate.valid_time(start_day):

                    members[role_id] = candidate
                    assigned_member.add(candidate.name)
                    match = True
                    break

            if not match:
                return []  # no member

        return [
            (members[role_id], role)
            for role_id, role in enumerate(project.roles)
        ]


def read_dataset(path):
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


def solve_naive(contributors, projects):

    hr = HumanResources(contributors)

    projects = sorted(projects, key=lambda p:
                      p.gain(p.start_day) / p.cost())

    output = dict()

    for project in tqdm(projects):
        conts_roles = hr.fill_roles(project, project.start_day)

        if len(conts_roles) == 0:
            continue

        project_start_day = max([cont.busy_until for cont, _ in conts_roles])

        for cont, role in conts_roles:
            cont.assign(project, role, project_start_day)

        output[project.name] = [cont for cont, _ in conts_roles]

    return output


def batch(projects, batch_size=10):
    for i in range(len(projects)-batch_size+1):
        for _ in range(5):  # try same batch 5 time
            yield projects[i: i+batch_size]


def solve_batch(contributors, projects):

    hr = HumanResources(contributors)

    projects = sorted(projects, key=lambda p: p.best_before + p.score)
    output = dict()

    for project_batch in tqdm(batch(projects), total=len(projects) * 5):
        project_batch = sorted(project_batch, key=lambda p:
                               p.gain(p.start_day) / p.cost())

        for project in project_batch:
            if project.name in output:
                continue

            conts_roles = hr.fill_roles(project, project.start_day)

            if len(conts_roles) == 0:
                continue

            project_start_day = max(
                [cont.busy_until for cont, _ in conts_roles])

            for cont, role in conts_roles:
                cont.assign(project, role, project_start_day)

            output[project.name] = [cont for cont, _ in conts_roles]

    return output


def write_solution(path, solution):

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
        contributors, projects = read_dataset('../input/' + i)
        # solution = solve_naive(contributors, projects)
        solution = solve_batch(contributors, projects)
        write_solution('../output/' + i, solution)


if __name__ == "__main__":
    main()
