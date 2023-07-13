## load libraries 
library(tidyverse)
library (readr)

## load data 
urlfile="https://raw.githubusercontent.com/ajstarks/dubois-data-portraits/master/challenge/challenge01/data.csv"

mydata<-read_csv(url(urlfile))

## create plot 
df <- mydata %>%
  select(Year, Colored, White) %>%
  gather(key = "variable", value = "value", -Year)

ggplot(df, aes(x = value, y = Year)) + 
  geom_path(aes(group=variable, linetype = variable)) + 
  
  scale_linetype_manual(values=c("solid", "longdash"))+ 
  scale_x_reverse(breaks = seq(0, 100, by = 5), expand = c(0,0)) + 
  scale_y_continuous(breaks = seq(1790, 1890, by = 10), expand = c(0,0)) +
  
  ggtitle("COMPARITIVE INCREASE OF WHITE AND COLORED \n POPULATION OF GEORGIA.") + 
  xlab("PERCENTS") +
  ylab("") + 
  
  theme(
    panel.background = element_rect(fill = "white", colour = "black", linetype = "solid"), 
    panel.grid.major = element_line(linewidth = 0.3, linetype = 'solid', colour = "lightpink"), 
    panel.grid.minor = element_blank(),
    
    plot.title = element_text(size=18, face="bold", hjust = 0.5),
    
    legend.position = "bottom",
    legend.key = element_rect(colour = NA, fill = NA), 
    legend.title = element_blank(),
    
    axis.text.x = element_text(colour = "gray25"),
    axis.title.x = element_text(colour = "gray25", vjust = -3.5), 
    axis.text.y = element_text(colour = "gray25"),
  )

## save plot 
ggsave("DeBois_Recreation.png", width = 8, height = 10) 
