library(tidyverse)
library(tseries)
library(zoo)

results_path <- "C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/results/Experiment_without_BH_test"
data_path <- "C:/Users/USER/OneDrive/Documents/PROJECTS/Cointegrated-pairs-trading/data"
test_data <- read.csv(
  file.path(data_path, "test_data.csv"),
  row.names = 1,
  check.names = FALSE
)

trade_results <- read.csv(
  file.path(results_path, "trade_results.csv"),
  check.names = FALSE
)

final_pairs <- read.csv(
  file.path(results_path, "ADF_passed_pairs.csv"),
  check.names = FALSE
)

dates <- as.Date(rownames(test_data))


best_pair <- trade_results %>%
  filter(
    `Sharpe ratio` > 1,
    `P-value(adf)` < 0.01,
    Win_rate > 75,
    `Max drawdown` > -0.05
  ) %>%
  arrange(desc(`Sharpe ratio`)) %>%
  slice(1)

if (nrow(best_pair) == 0) {
  stop("No pair found")
}

stock1 <- best_pair$Stock1
stock2 <- best_pair$Stock2

cat("Selected pair:", stock1, "/", stock2, "\n")


# Calculate the spread
pair_data <- final_pairs %>%
  filter(
    Pair1 == stock1,
    Pair2 == stock2
  )

if (nrow(pair_data) == 0) {
  stop("Pair not found in ADF results")
}

alpha <- pair_data$Alpha[1]
beta <- pair_data$Hedge_ratio[1]

spread <- test_data[[stock1]] -
  alpha -
  beta * test_data[[stock2]]

spread_clean <- na.omit(spread)


adf_result <- adf.test(spread_clean)

adf_p <- adf_result$p.value

cat("Test period ADF p-value:", adf_p, "\n")


spread_data <- data.frame(
  Date = dates,
  Spread = spread
)

p1 <- ggplot(spread_data, aes(x = Date, y = Spread)) +
  geom_line(color = "steelblue") +
  geom_hline(
    yintercept = mean(spread, na.rm = TRUE),
    linetype = "dashed"
  ) +
  labs(
    title = paste(stock1, "/", stock2, "Spread"),
    subtitle = paste("Test period ADF p-value =", round(adf_p, 4)),
    x = "Date",
    y = "Spread"
  ) +
  theme_minimal()

ggsave(
  file.path(
    results_path,
    paste0(
      tolower(stock1), "_",
      tolower(stock2), "_spread.png"
    )
  ),
  p1,
  width = 8,
  height = 4
)

# ACF of the spread

acf_result <- acf(
  spread_clean,
  lag.max = 30,
  plot = FALSE
)

acf_data <- data.frame(
  Lag = as.numeric(acf_result$lag)[-1],
  ACF = as.numeric(acf_result$acf)[-1]
)

confidence <- 1.96 / sqrt(length(spread_clean))

p2 <- ggplot(acf_data, aes(x = Lag, y = ACF)) +
  geom_col(fill = "steelblue") +
  geom_hline(
    yintercept = c(-confidence, confidence),
    linetype = "dashed"
  ) +
  geom_hline(yintercept = 0) +
  labs(
    title = paste("ACF of", stock1, "/", stock2, "Spread"),
    x = "Lag",
    y = "Autocorrelation"
  ) +
  theme_minimal()

ggsave(
  file.path(
    results_path,
    paste0(
      tolower(stock1), "_",
      tolower(stock2), "_acf.png"
    )
  ),
  p2,
  width = 7,
  height = 4
)


# Same vs Cross Industry

same_industry <- trade_results %>%
  filter(Industry_type == "Same") %>%
  pull(`Sharpe ratio`) %>%
  na.omit()

cross_industry <- trade_results %>%
  filter(Industry_type == "Cross") %>%
  pull(`Sharpe ratio`) %>%
  na.omit()


# t-test
test <- t.test(
  same_industry,
  cross_industry
)

cat("\nIndustry comparison\n")
cat(
  "Same industry mean:",
  mean(same_industry),
  "\n"
)

cat(
  "Cross industry mean:",
  mean(cross_industry),
  "\n"
)

cat(
  "T-test p-value:",
  test$p.value,
  "\n"
)


industry_data <- trade_results %>%
  filter(
    Industry_type == "Same" |
      Industry_type == "Cross"
  )

industry_data$Industry <- ifelse(
  industry_data$Industry_type == "Same",
  "Same Industry",
  "Cross Industry"
)

p3 <- ggplot(
  industry_data,
  aes(
    x = Industry,
    y = `Sharpe ratio`
  )
) +
  geom_boxplot() +
  geom_jitter(width = 0.15) +
  geom_hline(
    yintercept = 0,
    linetype = "dashed"
  ) +
  labs(
    title = "Same Industry vs Cross Industry",
    x = "",
    y = "Sharpe Ratio"
  ) +
  theme_minimal()

ggsave(
  file.path(
    results_path,
    "industry_comparison.png"
  ),
  p3,
  width = 7,
  height = 5
)


# Calculate Z-score

rolling_mean <- rollmean(
  spread,
  30,
  fill = NA,
  align = "right"
)

rolling_sd <- rollapply(
  spread,
  30,
  sd,
  fill = NA,
  align = "right"
)

zscore <- (
  spread - rolling_mean
) / rolling_sd

zscore <- na.omit(zscore)


zscore_data <- data.frame(
  Zscore = zscore
)

p4 <- ggplot(
  zscore_data,
  aes(x = Zscore)
) +
  geom_histogram(
    bins = 40,
    fill = "steelblue",
    color = "white"
  ) +
  geom_vline(
    xintercept = c(-2, 2),
    linetype = "dashed"
  ) +
  geom_vline(
    xintercept = c(-3.5, 3.5),
    linetype = "dotted"
  ) +
  labs(
    title = paste(
      "Z-score Distribution:",
      stock1,
      "/",
      stock2
    ),
    x = "Z-score",
    y = "Count"
  ) +
  theme_minimal()

ggsave(
  file.path(
    results_path,
    paste0(
      tolower(stock1), "_",
      tolower(stock2), "_zscore_dist.png"
    )
  ),
  p4,
  width = 7,
  height = 4
)


cat("Pair:", stock1, "/", stock2, "\n")
cat("ADF p-value:", adf_p, "\n")
cat("Same industry mean Sharpe:", mean(same_industry), "\n")
cat("Cross industry mean Sharpe:", mean(cross_industry), "\n")
cat("Industry t-test p-value:", test$p.value, "\n")
