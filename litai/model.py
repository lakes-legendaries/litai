"""Article ranking model"""

from __future__ import annotations

from typing import Any

from nptyping import NDArray
from pandas import DataFrame
from sklearn.linear_model import LinearRegression
from vhash import VHash


class TokenRegressor:
    """Article Ranking Model

    Parameters
    ----------
    fast: bool, optional, default=False
        If True, use a LinearRegressor, instead of LinearSVR, for speed.
    """

    def fit(
        self,
        /,
        X: DataFrame,
        y: NDArray[(Any,), float],
    ) -> TokenRegressor:
        """Fit model

        Parameters
        ----------
        X: DataFrame
            Articles to use for fitting
        y: NDArray[(Any,), float]
            Label for each article
        """
        text = self.__class__._get_text(X)
        self._tokenizer = VHash().fit(text, y)
        numeric = self._tokenizer.transform(text)
        self._model = LinearRegression().fit(numeric, y)
        return self

    def predict(
        self,
        /,
        X: DataFrame,
    ) -> NDArray[(Any,), float]:
        """Score articles

        Parameters
        ----------
        X: DataFrame
            Articles to score
        """
        text = self.__class__._get_text(X)
        numeric = self._tokenizer.transform(text)
        return self._model.predict(numeric)

    @classmethod
    def _get_text(cls, df: DataFrame) -> list[str]:
        """Preprocess dataframe for VHash model

        Parameters
        ----------
        df: DataFrame
            Articles to process

        Returns
        -------
        list[str]
            Text from articles
        """
        return [
            f"{row['Title']} {row['Abstract']} {row['Keywords']}"
            for _, row in df.iterrows()
        ]
