from terminalbench.tasks.loader import load_tasks


def test_bank_shape():
    tasks = load_tasks()
    assert len(tasks) == 60
    repos = {task.repo for task in tasks}
    assert repos == {
        "pallets/click",
        "Textualize/rich",
        "httpie/cli",
        "BurntSushi/ripgrep",
        "sharkdp/fd",
    }
    for repo in repos:
        group = [task for task in tasks if task.repo == repo]
        assert len(group) == 12
        assert sum(task.split == "train" for task in group) == 5
        assert sum(task.split == "held_out" for task in group) == 7
    assert sum(task.split == "train" for task in tasks) == 25
    assert sum(task.split == "held_out" for task in tasks) == 35
    assert sum(task.fixture is not None for task in tasks) == 5
