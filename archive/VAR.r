# Load required libraries
library(vars)
library(urca)
library(lmtest)
library(ggplot2)
library(gridExtra)
library(dplyr)

# Load data
df <- read.csv('eth_regression_data.csv')
df$week_start <- as.Date(df$week_start)
df <- df[order(df$week_start), ]

cat("Dataset shape:", nrow(df), "x", ncol(df), "\n")
cat("Date range:", as.character(min(df$week_start)), "to", as.character(max(df$week_start)), "\n\n")

# Select variables for analysis
vars_to_analyze <- c('weekly_vol_annualized', 'top1_centrality', 'top3_centrality', 
                     'top5_centrality', 'hhi', 'gini')

# Check stationarity with ADF test
cat(paste(rep("=", 50), collapse=""), "\n")
cat("STATIONARITY TESTS (ADF)\n")
cat(paste(rep("=", 50), collapse=""), "\n")

stationary_vars <- c()
analysis_data <- df

for(var in vars_to_analyze) {
  # Remove NA values for the test
  data_clean <- df[[var]][!is.na(df[[var]])]
  
  # ADF test
  adf_test <- ur.df(data_clean, type = "drift", selectlags = "AIC")
  adf_pvalue <- adf_test@teststat[1] > adf_test@cval[1,2]  # Compare with 5% critical value
  
  if(!adf_pvalue) {  # If stationary (reject null of unit root)
    stationary_vars <- c(stationary_vars, var)
    cat(var, ": Stationary\n")
  } else {
    # Create differenced variable
    diff_var <- paste0(var, "_diff")
    analysis_data[[diff_var]] <- c(NA, diff(df[[var]]))
    stationary_vars <- c(stationary_vars, diff_var)
    cat(var, ": Non-stationary (will difference)\n")
  }
}

cat("\nUsing variables:", paste(stationary_vars, collapse=", "), "\n")

# Prepare data for analysis (remove NA values)
analysis_data <- analysis_data[, c("week_start", stationary_vars)]
analysis_data <- na.omit(analysis_data)
cat("Final dataset shape:", nrow(analysis_data), "x", ncol(analysis_data)-1, "\n\n")

# GRANGER CAUSALITY TESTS (ALL PAIRWISE)
cat(paste(rep("=", 50), collapse=""), "\n")
cat("GRANGER CAUSALITY TESTS - ALL PAIRWISE\n")
cat(paste(rep("=", 50), collapse=""), "\n")

significant_pairs <- list()
all_significant_vars <- c()

# Test all pairwise combinations
for(i in 1:(length(stationary_vars)-1)) {
  for(j in (i+1):length(stationary_vars)) {
    var1 <- stationary_vars[i]
    var2 <- stationary_vars[j]
    
    cat("\nTesting", var1, "↔", var2, "\n")
    
    # Create bivariate dataset
    bivariate_data <- analysis_data[, c(var1, var2)]
    bivariate_data <- na.omit(bivariate_data)
    
    if(nrow(bivariate_data) < 20) {
      cat("Insufficient data, skipping...\n")
      next
    }
    
    tryCatch({
      # Determine optimal lag length
      max_lags <- min(4, floor(nrow(bivariate_data)/10))
      
      # Fit VAR for lag selection
      var_temp <- VAR(bivariate_data, p = max_lags, type = "const")
      lag_select <- VARselect(bivariate_data, lag.max = max_lags, type = "const")
      optimal_lag <- lag_select$selection["SC(n)"]  # Use Schwarz criterion (BIC)
      
      # Fit VAR with optimal lag
      var_model <- VAR(bivar