import pytest

from screen import Screen


@pytest.fixture(name='screen', scope='function')
def screen_fixture():
    screen = Screen()
    yield screen



def test_draw_pixel_on_screen():
    pass
