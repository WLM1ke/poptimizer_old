# Оптимизация долгосрочного портфеля акций

[![Build Status](https://travis-ci.org/WLM1ke/PortfolioOptimizer.svg?branch=master)](https://travis-ci.org/WLM1ke/PortfolioOptimizer) [![codecov](https://codecov.io/gh/WLM1ke/PortfolioOptimizer/branch/master/graph/badge.svg)](https://codecov.io/gh/WLM1ke/PortfolioOptimizer)


## Цель
Воспроизвести на базе Python существующую модель управления долгосрочным инвестиционным портфелем российских акций на базе Excel и усовершенствовать ее с помощью автоматизации загрузки данных и методов машинного обучения

## Этапы работы
1. Пакет [download](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio/download) -  функции-загрузчики необходимых данных из интернета:
- [x] CPI [источник данных](http://www.gks.ru/) - **cpi()**
- [x] Дивиденды [источник данных](https://www.dohod.ru/) - **dividends(ticker)**
- [x] История котировок акций [источник данных](https://www.moex.com) - **quotes_history(ticker, start_date)** и **index_history_from_start(ticker)**
- [x] Итория значений индекса MOEX Russia Net Total Return (Resident) [источник данных](https://www.moex.com/ru/index/totalreturn.aspx) - **index_history(ticker, start_date)** и **index_history_from_start(ticker)**
- [x] Информация по кратким наименованиям, регистрационным номерам, размерам лотов и последним ценам [источник данных](https://www.moex.com)- **securities_info(tickers)**
- [x] Тикеры, соответсвующие регистрационному номеру [источник данных](https://www.moex.com) - **tickers(reg_number)**

2. Пакет [getter](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio/getter) - функции, обновляющие и загружающие локальную версию данных:
- [ ] CPI
- [x] Дивиденды - статические данные существующей модели
- [ ] Дивиденды - динамические данные из интернета
- [x] История котировок акций
- [ ] Итория значений индекса MOEX Russia Net Total Return (Resident)
- [x] Информация по кратким наименованиям, регистрационным номерам, альтернативным тикерам, размерам лотов и последним ценам

3. Трансформация данных:
- [ ] Пересчет в реальные показатели
- [ ] Перевод в месячные таймфреймы

4. Ключевы метрики портфеля:
- [ ] Простой DGP для волатильности и доходности портфеля
- [ ] Метрики дивидендного потока
- [ ] Метрики стоимости потортфеля

5. Оптимизационная процедура:
- [ ] Доминирование по Парето
- [ ] Выбор оптимального направления
  
6. Усовершенстование существующей модели:
- [ ] Скользящий месячный таймфрейм
- [ ] Скользящий таймфрейм по дивидендам
- [ ] Применение ML
