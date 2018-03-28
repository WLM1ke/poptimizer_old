# Оптимизация долгосрочного портфеля акций

[![Build Status](https://travis-ci.org/WLM1ke/PortfolioOptimizer.svg?branch=master)](https://travis-ci.org/WLM1ke/PortfolioOptimizer)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/18d7bd2be5f34466b1884250ffea3066)](https://www.codacy.com/app/wlmike/PortfolioOptimizer?utm_source=github.com&utm_medium=referral&utm_content=WLM1ke/PortfolioOptimizer&utm_campaign=Badge_Coverage)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/18d7bd2be5f34466b1884250ffea3066)](https://www.codacy.com/app/wlmike/PortfolioOptimizer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=WLM1ke/PortfolioOptimizer&amp;utm_campaign=Badge_Grade)
[![BCH compliance](https://bettercodehub.com/edge/badge/WLM1ke/PortfolioOptimizer?branch=master)](https://bettercodehub.com/)
[![CodeFactor](https://www.codefactor.io/repository/github/wlm1ke/portfoliooptimizer/badge)](https://www.codefactor.io/repository/github/wlm1ke/portfoliooptimizer)

## Цель
Воспроизвести на базе Python существующую модель управления долгосрочным инвестиционным портфелем российских акций на базе Excel и усовершенствовать ее с помощью автоматизации загрузки данных и методов машинного обучения

## Этапы работы
1. Пакет [download](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio/download) -  функции-загрузчики необходимых данных из интернета, которые используются пакетом getter для создания локальных данных. Функции максимально приближены к API выдачи данных, поэтому принимают иногда набор тикеров, а иногда отдельный тикер:
- [x] CPI [источник данных](http://www.gks.ru/) - **cpi()**
- [x] Дивиденды [источник данных](https://www.dohod.ru/) - **nominal_retax_dividends(ticker)**
- [x] История котировок акций [источник данных](https://www.moex.com) - **quotes_history(ticker, start_date)**
- [x] История значений индекса MOEX Russia Net Total Return (Resident) [источник данных](https://www.moex.com/ru/index/totalreturn.aspx) - **index_history(ticker, start_date)**
- [x] Информация по кратким наименованиям, регистрационным номерам, размерам лотов и последним ценам [источник данных](https://www.moex.com)- **securities_info(tickers)**
- [x] Тикеры, соответствующие регистрационному номеру [источник данных](https://www.moex.com) - **reg_number_tickers(reg_number)**

2. Пакет [getter](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio/getter) - функции, обновляющие и загружающие локальную версию данных, используя информацию загруженную с помощью функций из пакета getter. Функции максимально унифицированы - принимают в качестве аргумента набор тикеров:
- [x] CPI - **cpi()**
- [x] 'Старые' дивиденды (статические данные существующей модели - загружаются из локального xlsx-файла) - **legacy_dividends(tickers)**
- [x] Дивиденды (данные обновляются из интернета) - **nominal_retax_dividends(tickers)**
- [x] История цен закрытия акций - **prices_history(tickers)**
- [x] История объемов торгов акций - **volumes_history(tickers)**
- [x] История значений индекса MOEX Russia Net Total Return (Resident) - **index_history()**
- [x] Информация по кратким наименованиям, регистрационным номерам, альтернативным тикерам, размерам лотов и последним ценам - **security_info(tickers)**
- [x] Последние цены акций - **last_prices(tickers)**

4. Реализация базового класса портфеля:
- [ ] Конструктор
- [ ] Данные
- [ ] Методы

3. Метрики доходности:
- [ ] Трансформация доходностей в месячные таймфреймы
- [ ] Простой DGP для волатильности и доходности портфеля
- [ ] Метрики стоимости портфеля

5. Метрики дивидендного потока:
- [ ] Пересчет дивидендов в реальные показатели
- [ ] Метрики дивидендного потока

6. Оптимизационная процедура:
- [ ] Доминирование по Парето
- [ ] Выбор оптимального направления модификации структуры портфеля
  
7. Усовершенствование существующей модели:
- [ ] Скользящий месячный таймфрейм
- [ ] Скользящий таймфрейм по дивидендам
- [ ] Бэктестирование - возможно нужно добавить методы покупки/продажи, прихода дивидендов, перевода даты, издержек и импакта, и данные для отслеживания метрик портфеля в динамике
- [ ] Применение ML
