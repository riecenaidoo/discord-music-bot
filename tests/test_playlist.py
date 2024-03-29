import unittest

from bot.playlist import Playlist


class TestMusicQueue(unittest.TestCase):

    def test_normal_next(self):
        playlist = Playlist()
        playlist.add("a")
        playlist.add("b")
        playlist.add("c")

        self.assertEqual(playlist.next(), "a")
        self.assertEqual(playlist.next(), "b")
        self.assertEqual(playlist.next(), "c")
        try:
            playlist.next()
            self.fail("Should throw an error!")
        except Playlist.ExhaustedException:
            pass

    def test_loop_next(self):
        playlist = Playlist()
        playlist.add("a")
        playlist.add("b")
        playlist.add("c")
        playlist.loop_mode()

        self.assertEqual(playlist.next(), "a")
        self.assertEqual(playlist.next(), "b")
        self.assertEqual(playlist.next(), "c")
        self.assertEqual(playlist.next(), "a")
        self.assertEqual(playlist.next(), "b")
        self.assertEqual(playlist.next(), "c")

    def test_repeat_next(self):
        playlist = Playlist()
        playlist.add("a")
        playlist.add("b")
        playlist.add("c")
        playlist.repeat_mode()

        self.assertEqual(playlist.next(), "a")
        self.assertEqual(playlist.next(), "a")
        self.assertEqual(playlist.next(), "a")

    def test_prev(self):
        playlist = Playlist()
        playlist.add("a")
        playlist.add("b")
        playlist.next()  # Playing a
        try:
            playlist.prev()
            self.fail(
                "Should throw an error! There is no previous song. 'a' is currently playing!")
        except Playlist.ExhaustedException:
            pass

        playlist.next()  # Playing b
        self.assertEqual(playlist.prev(), "a")

        try:
            playlist.prev()
            self.fail(
                "Should throw an error! There is no previous song before 'a'.")
        except Playlist.ExhaustedException:
            pass
