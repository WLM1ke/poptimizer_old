# Оптимизация долгосрочного портфеля акций

[![Build Status](https://travis-ci.org/WLM1ke/PortfolioOptimizer?branch=master)](https://travis-ci.org/WLM1ke/PortfolioOptimizer) [![codecov](https://codecov.io/gh/WLM1ke/PortfolioOptimizer/branch/master/graph/badge.svg)](https://codecov.io/gh/WLM1ke/PortfolioOptimizer)

## Основная цель:
Воспроизвести на базе Python существующую модель управления долгосрочным инвестиционным портфелем российских акций на базе Excel и усовершенствовать ее с помощью автоматизации загрузки данных и методов машинного обучения

## Основные этапы:
1. Загрузчики необходимых данных
  * Котировки акций
  * CPI
  * Дивиденды
  * Индекс полной доходности

2. Трансформация данных
  * Пересчет в реальные показатели
  * Перевод в месячные таймфреймы

3. Ключевы метрики портфеля
  * Простой DGP для волатильности и доходности портфеля
  * Метрики дивидендного потока
  * Метрики стоимости потортфеля

4. Оптимизационная процедура
  * Доминирование по Парето
  * Выбор оптимального направления
  
5. Усовершенстование существующей модели
  * Скользящий месячный таймфрейм
  * Скользящий таймфрейм по дивидендам
  * Применение ML
