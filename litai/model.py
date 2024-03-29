"""Article ranking model"""

from __future__ import annotations

from typing import Any

from nptyping import NDArray
from pandas import DataFrame
from sklearn.linear_model import LinearRegression
from vhash import VHash


class TokenRegressor:
    """Article Ranking Model

    This model uses the vhash package to perform fast vector quantization of
    documents, and then uses an sklearn LinearRegression model to score
    articles.

    Parameters
    ----------
    model: Any, optional, default=sklearn.linear_model.LinearRegression()
        Model to use for fitting. Pass initialized (which exposes constructor
        to the calling user), e.g.

        .. code-block:: python

           tr = TokenRegressor(model=LinearSVR(max_iter=1E6))
    """
    def __init__(
        self,
        /,
        *,
        model: Any = LinearRegression(),
    ):
        self._model = model

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
        self._model.fit(numeric, y)
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
