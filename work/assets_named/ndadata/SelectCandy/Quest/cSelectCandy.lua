-- 이 스크립트 에서는 다음과 같이 가정합니다
-- NumberData.Log1 : 처음에 선택했던 캔디
-- NumberData.Log2 : 처음에 선택했던 캔디 수량
-- NumberData.Log3 : start time
-- NumberData.Log4 : 퀘스트 연 시간?
-- NumberData.Log5 : 퀘스트 받은 횟수 (1000 자리) + 퀘스트 완료 횟수(1자리)
-- NumberData.Log6 : 2~3일 이내에 접속했는지( 보상, 완료 )

NumberData = {}
StringData = {}

ItemImg = {}

ItemImg[0] = "Quest/Quest_2009_09_30_Item04.bmp"
ItemImg[1] = "Quest/Quest_2009_09_30_Item05.bmp"
ItemImg[2] = "Quest/Quest_2009_09_30_Item07.bmp"
ItemImg[3] = "Quest/Quest_2009_09_30_Item03.bmp"
ItemImg[4] = "Quest/Quest_2009_09_30_Item01.bmp"
ItemImg[5] = "Quest/Quest_2009_09_30_Item02.bmp"
ItemImg[6] = "Quest/Quest_2009_09_30_Item06.bmp"
ItemImg[7] = "Quest/Quest_2009_09_30_Item08.bmp"

itemname = {}

itemname[0] = "SelectCandy_RewardItem1"
itemname[1] = "SelectCandy_RewardItem2"
itemname[2] = "SelectCandy_RewardItem3"
itemname[3] = "SelectCandy_RewardItem4"
itemname[4] = "SelectCandy_RewardItem5"
itemname[5] = "SelectCandy_RewardItem6"
itemname[6] = "SelectCandy_RewardItem7"
itemname[7] = "SelectCandy_RewardItem8"

function OnShowQuest()
	NumberData.IsSystemQuest = 1
	NumberData.UseDBString = 1
	
	--- quest's name
	StringData.QuestName = "SelectCandy"
	NumberData.Back_Count = 1
	
	--- back image
	NumberData.Back_Visible = 1
	
	--- list button
	NumberData.QuestBtn_Visible = 1
	StringData.QuestBtn_Path = "Quest/Quest_2009_09_30_List.bmp"	
	
	StringData.Back_Path = "Quest/Quest_2009_09_30_Back.jpg"
	
	--- done button
	NumberData.DoneBtn_Count = 1
	
	NumberData.DoneBtn00_Visible = 0
	StringData.DoneBtn00_Path = "Quest/Quest_2009_09_30_Bt.bmp"
	NumberData.DoneBtn00_PosX = 174
	NumberData.DoneBtn00_PosY = 269
	
	--- images
	NumberData.Img_Count = 1
	
	StringData.Img00_Path = ""
	NumberData.Img00_Frame = 0
	NumberData.Img00_PosX = 98
	NumberData.Img00_PosY = 278	
	
	NumberData.Msg_Count = 2
	
	-- explanation messages upto 2
	NumberData.Msg00_Style = 3
	NumberData.Msg00_TextColor = GetColor(205, 116, 0)
	NumberData.Msg00_OutlineColor = 0
	NumberData.Msg00_PosX = 83
	NumberData.Msg00_PosY = 147
	NumberData.Msg00_Height = 15
	StringData.Msg00_Content = ""
	
	NumberData.Msg01_Style = 3
	NumberData.Msg01_TextColor = GetColor(1, 60, 0)
	NumberData.Msg01_OutlineColor = 0
	NumberData.Msg01_PosX = 85
	NumberData.Msg01_PosY = 240	
	StringData.Msg01_Content = ""	
	
	-- 퀘스트 미 시작시
	if NumberData.QuestState == 0 then
		return 0		
	end	
	
	if ( NumberData.Log6 == 2 )			-- 완료했으면
	then			
		StringData.Back_Path = "Quest/Quest_2009_09_30_End.jpg"
		NumberData.Msg00_PosX = 84
		NumberData.Msg00_PosY = 190	
		StringData.Img00_Path = ItemImg[NumberData.Log1-90000]
		return 0
	elseif ( NumberData.Log6 == 1 )		-- 선물  보상  기간내이면.
	then
		StringData.Back_Path = "Quest/Quest_2009_09_30_End.jpg"		
		NumberData.DoneBtn00_Visible = 1						
		StringData.Img00_Path = ItemImg[NumberData.Log1-90000]		
		return 0
	end
	
	-- 여기서부터는 퀘스트 시작일부터 보상일 사이!!		
	CurrentDate = os.date("*t", NumberData.Log4)	
	QuestStartDate = os.date("*t", NumberData.Log3)
	WeekDay = QuestStartDate.wday	
			
	local CandyTime = os.time({year = QuestStartDate.year, month = QuestStartDate.month, day = QuestStartDate.day, hour = 0, min = 0, sec = 0})	
	local rewardStartTime = 0			-- 보상 첫째날
  	local rewardEndTime = 0				-- 보상 둘째날
  	local oneDay = 86400			-- 60 * 60 * 24 (초) ( 하루 )
  	
	if ( QuestStartDate.wday == 4 ) 		-- 수요일 
  	then
  		rewardStartTime = CandyTime + ( oneDay * 3 )
  		rewardEndTime = CandyTime + ( oneDay * 4 ) 				  		  			  		  		  	
  	elseif ( QuestStartDate.wday == 6 ) 	-- 금요일 
  	then
  		rewardStartTime = CandyTime + ( oneDay * 1 )
  		rewardEndTime = CandyTime + ( oneDay * 2 )
  	else
  		rewardStartTime = CandyTime + ( oneDay * 2 )
  		rewardEndTime = CandyTime + ( oneDay * 3 )  	
  	end 	 
  	---		
	
	-- wday : 1 = 일, 2 = 월, 3 = 화, 4 = 수, 5 = 목, 6 = 금, 7 = 토	
	if ( WeekDay ~= 4 or WeekDay ~= 5 or WeekDay ~= 6 )		-- 주말에 보상 받지 않으면 요일 문구 출력
	then
		-- ex) 수요일이나 목요일에 다시 찾아오라구! \n자네가 갖고 싶은 선물을 준비해둘게~
		local DayOfWeek = 
		{ 	
			"SelectCandy_Sun", "SelectCandy_Mon", "SelectCandy_Tue", "SelectCandy_Wed", 
			"SelectCandy_Thur", "SelectCandy_Fri", "SelectCandy_Sat" 
		}
		local rewardStartDate = os.date("*t", rewardStartTime)	
		local rewardEndDate = os.date("*t", rewardEndTime)		
		
		StringData.Msg00_Content = DayOfWeek[rewardStartDate.wday]		
		StringData.Msg01_Content = "SelectCandy_Or"
		StringData.Msg02_Content = DayOfWeek[rewardEndDate.wday]
		StringData.Msg03_Content = "SelectCandy_BeforeEndB1_1"
		StringData.Msg04_Content = "SelectCandy_BeforeEndB1_2"		
	else
		-- ex) 수요일이나 목요일에 꼭 다시 찾아오라구! \n자네가 원하는 선물을 준비해둘게~
		StringData.Msg00_Content = "SelectCandy_Sat"
		StringData.Msg01_Content = "SelectCandy_Or"
		StringData.Msg02_Content = "SelectCandy_Sun"
		StringData.Msg03_Content = "SelectCandy_BeforeEndB1_3"
		StringData.Msg04_Content = "SelectCandy_BeforeEndB1_4"		
	end	
	
	NumberData.Msg_Count = 5
	
	-- X요일
	NumberData.Msg00_Style = 5
	NumberData.Msg00_TextColor = GetColor(255, 240, 1)
	NumberData.Msg00_OutlineColor = GetColor(25, 96, 4)
	NumberData.Msg00_PosX = 99
	NumberData.Msg00_PosY = 238	
	
	-- 이나
	NumberData.Msg01_Style = 2
	NumberData.Msg01_TextColor = GetColor(199, 255, 115)
	NumberData.Msg01_OutlineColor = GetColor(25, 96, 4)
	NumberData.Msg01_PosX = 136
	NumberData.Msg01_PosY = 238
	
	-- X요일
	NumberData.Msg02_Style = 5
	NumberData.Msg02_TextColor = GetColor(255, 240, 1)
	NumberData.Msg02_OutlineColor = GetColor(25, 96, 4)
	NumberData.Msg02_PosX = 165
	NumberData.Msg02_PosY = 238
	
	-- 에 다시 찾아오라구!
	NumberData.Msg03_Style = 2
	NumberData.Msg03_TextColor = GetColor(199, 255, 115)
	NumberData.Msg03_OutlineColor = GetColor(25, 96, 4)
	NumberData.Msg03_PosX = 202
	NumberData.Msg03_PosY = 238
	
	-- 자네가 원하는 선물을 준비해둘게~ or 자네가 원하는 선물을 준비해둘게
	NumberData.Msg04_Style = 0
	NumberData.Msg04_TextColor = GetColor(9, 39, 1)
	NumberData.Msg04_OutlineColor = 0
	NumberData.Msg04_PosX = 99
	NumberData.Msg04_PosY = 257		

	return 0	
end

function OnNaviButtonClicked()
    return 0
end

function GetColor(red, green, blue)
	color = (red * 65536) + (green * 256) + blue
	return color
end

