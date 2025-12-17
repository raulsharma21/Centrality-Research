#### Set working directory ####
setwd("~/Documents/Github/Centrality-Research")

#### Load libraries ####
library(readtext)
library(stringi)
library(stringr)
library(knitr)
library(readr)
library(data.table)
library(RecordLinkage)
library(tidyquant)
library(RSQLite)
library(dbplyr)
library(RPostgres)
library(bizdays)
library(timeDate)
library(tidyverse)
library(readxl)
library(frenchdata)
library(RColorBrewer)
library(igraph)
library(glmnet)
library(survey)
library(doParallel)
library(parallel)
require(lubridate)
library(dynlm)
library(matrixStats)
library(vars)
library(dplyr)

#### Parallelize ####
stopImplicitCluster()
registerDoParallel(cores = 3)


#### Read data ####
data = read_csv("eth_regression_data.csv")

data$top1_centrality_diff = c(NA, data$top1_centrality[2:nrow(data)] - data$top1_centrality[1:(nrow(data)-1)])
data$top3_centrality_diff = c(NA, data$top3_centrality[2:nrow(data)] - data$top3_centrality[1:(nrow(data)-1)])
data$top5_centrality_diff = c(NA, data$top5_centrality[2:nrow(data)] - data$top5_centrality[1:(nrow(data)-1)])
data$top10_centrality_diff = c(NA, data$top10_centrality[2:nrow(data)] - data$top10_centrality[1:(nrow(data)-1)])
data$hhi_diff = c(NA, data$hhi[2:nrow(data)] - data$hhi[1:(nrow(data)-1)])
data$gini_diff = c(NA, data$gini[2:nrow(data)] - data$gini[1:(nrow(data)-1)])

data$weekly_vol_annualized_diff = c(NA, diff(data$weekly_vol_annualized))

n_ahead_here = 18

#### VAR (orthogonal shocks) ####

# endogenous variables (what we want to predict/analyze)
endog_vars = c("weekly_vol_annualized_diff", "weekly_mean_return", 
               "market_weekly_vol_annualized", "market_weekly_return", 
               "eth_weekly_turnover", "market_weekly_turnover")

# network/centrality variables (the predictors)
network_vars = c("hhi_diff")
                 # "top3_centrality_diff", "top5_centrality_diff", 
                 # "top10_centrality_diff", "hhi_diff", "gini_diff")
id_ordering = c(endog_vars, network_vars)
variables_var = na.omit(data[,id_ordering])
variables_var = scale(variables_var)

VAR_all = VAR(variables_var, p = 1, type = "const")

irf_orth = list()

pb = txtProgressBar(min = 0, max = length(endog_vars), initial = 0, style = 3)
irf_orth = foreach(i = 1:length(endog_vars), .errorhandling = 'stop') %dopar% {
  var_here = endog_vars[i]
  res = list()
  res[[1]] = irf(VAR_all, impulse = "hhi_diff", n_ahead_here, response = var_here, runs = 1000, ci = 0.95, cumulative = TRUE, plot = FALSE, orth = TRUE)
  # res[[2]] = irf(VAR_all, impulse = "top3_centrality_diff", n_ahead_here, response = var_here, runs = 100, ci = 0.95, cumulative = TRUE, plot = FALSE, orth = TRUE)
  # res[[3]] = irf(VAR_all, impulse = "top5_centrality_diff", n_ahead_here, response = var_here, runs = 100, ci = 0.95, cumulative = TRUE, plot = FALSE, orth = TRUE)
  setTxtProgressBar(pb, i)
  res
}
names(irf_orth) = endog_vars

#### Impulse response functions ####

labels = c("ETH Weekly Volatility", "ETH Weekly Return", "ETH Absolute Return", "Market Weekly Volatility", "Market Weekly Return", "ETH Weekly Turnover", "Market Weekly Turnover")
names(labels) = c("weekly_vol_annualized_diff", "weekly_mean_return", "weekly_abs_return", "market_weekly_vol_annualized", "market_weekly_return", "eth_weekly_turnover", "market_weekly_turnover")
labels_x = 1:(n_ahead_here+1)
labels_x_char = 0:n_ahead_here

plot_here = 1
png("R_Corrected_top3.png", width = 7.5, height = 4, units = "in", res = 200)
# par(mfrow = c(4,2))

# for (i in 1:length(endog_vars)) {
  i = 1
  var_here = endog_vars[i]
  irf_here = irf_orth[[var_here]][[plot_here]]
  M_here = max(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
  m_here = min(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
  labels_y = pretty(range(c(m_here, M_here)))
  labels_y_char = as.character(labels_y)
  par(cex = 0.55, mar = c(4.1, 2.1, 2.1, 3.1))
  plot(irf_here$irf[[1]], type="n", ylim = c(m_here, M_here), ylab = "", xlab = "Weeks ahead", main = labels[var_here], axes = FALSE)
  axis(1, at = labels_x, labels = labels_x_char)
  axis(2, at = labels_y, labels = labels_y_char)
  polygon(c(1:length(irf_here$Upper[[1]]), length(irf_here$Lower[[1]]):1), c(irf_here$Upper[[1]], rev(irf_here$Lower[[1]])),  col = "#ddcba4", border = NA)
  lines(irf_here$irf[[1]], col = "#862633")
  #lines(irf_here$Lower[[1]], col = "darkgrey", lty = "solid")
  #lines(irf_here$Upper[[1]], col = "darkgrey", lty = "solid")
  abline(h=0)
# }

dev.off()

# plot_here = 2
# png("irf_first.png", width = 7.5, height = 8, units = "in", res = 200)
# par(mfrow = c(4,2))
# 
# 
# for (i in 1:length(endog_vars)) {
#   var_here = endog_vars[i]
#   irf_here = irf_orth[[var_here]][[plot_here]]
#   M_here = max(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
#   m_here = min(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
#   labels_y = pretty(range(c(m_here, M_here)))
#   labels_y_char = as.character(labels_y)
#   par(cex = 0.55, mar = c(4.1, 2.1, 2.1, 3.1))
#   plot(irf_here$irf[[1]], type="n", ylim = c(m_here, M_here), ylab = "", xlab = "Months ahead", main = labels[var_here], axes = FALSE)
#   axis(1, at = labels_x, labels = labels_x_char)
#   axis(2, at = labels_y, labels = labels_y_char)
#   polygon(c(1:length(irf_here$Upper[[1]]), length(irf_here$Lower[[1]]):1), c(irf_here$Upper[[1]], rev(irf_here$Lower[[1]])),  col = "#ddcba4", border = NA)
#   lines(irf_here$irf[[1]], col = "#862633")
#   #lines(irf_here$Lower[[1]], col = "darkgrey", lty = "solid")
#   #lines(irf_here$Upper[[1]], col = "darkgrey", lty = "solid")
#   abline(h=0)
# }
# 
# dev.off()
# 
# 
# plot_here = 3
# png("irf_second.png", width = 7.5, height = 8, units = "in", res = 200)
# par(mfrow = c(4,2))
# 
# 
# for (i in 1:length(endog_vars)) {
#   var_here = endog_vars[i]
#   irf_here = irf_orth[[var_here]][[plot_here]]
#   M_here = max(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
#   m_here = min(irf_here$irf[[1]], irf_here$Lower[[1]], irf_here$Upper[[1]], 0)
#   labels_y = pretty(range(c(m_here, M_here)))
#   labels_y_char = as.character(labels_y)
#   par(cex = 0.55, mar = c(4.1, 2.1, 2.1, 3.1))
#   plot(irf_here$irf[[1]], type="n", ylim = c(m_here, M_here), ylab = "", xlab = "Months ahead", main = labels[var_here], axes = FALSE)
#   axis(1, at = labels_x, labels = labels_x_char)
#   axis(2, at = labels_y, labels = labels_y_char)
#   polygon(c(1:length(irf_here$Upper[[1]]), length(irf_here$Lower[[1]]):1), c(irf_here$Upper[[1]], rev(irf_here$Lower[[1]])),  col = "#ddcba4", border = NA)
#   lines(irf_here$irf[[1]], col = "#862633")
#   #lines(irf_here$Lower[[1]], col = "darkgrey", lty = "solid")
#   #lines(irf_here$Upper[[1]], col = "darkgrey", lty = "solid")
#   abline(h=0)
# }
# 
# dev.off()

# 
# plot(data$weekly_vol_annualized, type="l", main="ETH Volatility")
# plot(data$eth_weekly_turnover, type="l", main="ETH Turnover")
# plot(data$top3_centrality, type="l", main="Top3 Centrality")
