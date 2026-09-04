import unittest
from searchers.aladin_searcher import AladinSearcher
from searchers.kyobo_searcher import KyoboSearcher
from searchers.daegu_lib_searcher import DaeguLibSearcher
from searchers.yu_lib_searcher import YULibSearcher
from searchers.ai_recommender import AIRecommender

class TestSearchers(unittest.TestCase):
    def test_aladin_search(self):
        s = AladinSearcher()
        res = s.search_books("소년이 온다", max_results=3)
        print(f"\n[Test] Aladin found {len(res)} books")
        self.assertTrue(isinstance(res, list))

    def test_kyobo_search(self):
        s = KyoboSearcher()
        res = s.search_books("소년이 온다", max_results=3)
        print(f"\n[Test] Kyobo found {len(res)} books")
        self.assertTrue(isinstance(res, list))

    def test_yu_lib_search(self):
        s = YULibSearcher()
        res = s.search_books("소년이 온다", max_results=3)
        print(f"\n[Test] YU Library found {len(res)} books")
        self.assertTrue(isinstance(res, list))

    def test_daegu_lib_search(self):
        s = DaeguLibSearcher()
        res = s.search_books("소년이 온다", max_results=3)
        print(f"\n[Test] Daegu Library found {len(res)} books")
        self.assertTrue(isinstance(res, list))

    def test_ai_recommender(self):
        s = AIRecommender()
        res = s.recommend_books("파이썬 코딩 입문 책 추천해줘")
        print(f"\n[Test] AI Recommender generated {len(res)} recommendations")
        self.assertTrue(len(res) > 0)

if __name__ == '__main__':
    unittest.main()
