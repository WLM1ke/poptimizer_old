# Оптимизация долгосрочного портфеля акций

[![Build Status](https://travis-ci.org/WLM1ke/PortfolioOptimizer.svg?branch=master)](https://travis-ci.org/WLM1ke/PortfolioOptimizer)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/18d7bd2be5f34466b1884250ffea3066)](https://www.codacy.com/app/wlmike/PortfolioOptimizer?utm_source=github.com&utm_medium=referral&utm_content=WLM1ke/PortfolioOptimizer&utm_campaign=Badge_Coverage)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/18d7bd2be5f34466b1884250ffea3066)](https://www.codacy.com/app/wlmike/PortfolioOptimizer?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=WLM1ke/PortfolioOptimizer&amp;utm_campaign=Badge_Grade)
[![BCH compliance](https://bettercodehub.com/edge/badge/WLM1ke/PortfolioOptimizer?branch=master)](https://bettercodehub.com/)
[![CodeFactor](https://www.codefactor.io/repository/github/wlm1ke/portfoliooptimizer/badge)](https://www.codefactor.io/repository/github/wlm1ke/portfoliooptimizer)
[![codebeat badge](https://codebeat.co/badges/104a3651-e8cb-4df9-aad5-ca7b4b38099a)](https://codebeat.co/projects/github-com-wlm1ke-portfoliooptimizer-master)

## Цель
Воспроизвести на базе Python существующую модель управления долгосрочным инвестиционным портфелем российских акций на базе Excel и усовершенствовать ее с помощью автоматизации загрузки данных и методов машинного обучения

## Состав пакета
- Пакет [portfolio_optimizer.web](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio_optimizer/web) -  функции-загрузчики необходимых данных из интернета, которые используются пакетом local для создания локальных данных. Функции максимально приближены к web API выдачи данных, поэтому принимают иногда набор тикеров, а иногда отдельный тикер
- Пакет [portfolio_optimizer.local](https://github.com/WLM1ke/PortfolioOptimizer/tree/master/src/portfolio_optimizer/local) - функции, обновляющие и загружающие локальную версию данных, используя информацию загруженную с помощью функций из пакета web. Функции максимально унифицированы - принимают в качестве аргумента набор тикеров
- Класс [portfolio_optimizer.Portfolio](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/src/portfolio_optimizer/portfolio.py) - хранит информацию о составе портфеля
- Класс [portfolio_optimizer.DividendsMetrics](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/src/portfolio_optimizer/dividends_metrics.py) - осуществляет расчет ожидаемых годовых дивидендов портфеля и связанных с ними метрик риска
- Класс [portfolio_optimizer.ReturnsMetrics](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/src/portfolio_optimizer/returns_metrics.py) - осуществляет расчет ожидаемой доходности портфеля и связанных с ней рисков
- Класс [portfolio_optimizer.Optimizer](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/src/portfolio_optimizer/optimizer.py) - осуществляет оптимизацию портфеля по Парето на основе двух критериев повышения нижней границы доверительного интервала ожидаемых дивидендов и величины просадки 
- Модуль [portfolio_optimizer.settings](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/src/portfolio_optimizer/settings.py) - содержит глобальные настройки путей хранения данных и основных параметров оптимизации

## Использование
Большинство классов и функций содержат необходимые описания. 
Для ключевых классов реализована поддержка функции print, позволяющая распечатать сводные результаты анализа - [пример использования](https://github.com/WLM1ke/PortfolioOptimizer/blob/master/example_and_test.py) на реальном портфеле из нескольких десятков акций

## Дальнейшее развитие
- [ ] Реализация хранения данных о стоимости портфеля и составления ежемесячных pdf-отчетов
- [ ] Скользящий таймфрейм по дивидендам на основе web-данных
- [ ] Бэктестирование - возможно нужно добавить методы покупки/продажи, прихода дивидендов, перевода даты, издержек и импакта, и данные для отслеживания метрик портфеля в динамике
- [ ] Применение ML для прогнозирования вместо классических статистических методов
