------------------------------
-- 몬스터 랭크퀘스트
-- by jinn
--
-- Log1 : 문어맵 랭크
-- Log2 : 펭귄맵 랭크
-- Log3 : 물개맵 랭크
-- Log4 : 로봇맵 랭크
-- Log5 : 보상 받았는지 여부 ( 점수 )
-- Log6 : 진행중인 날짜
------------------------------

NumberData = {}
StringData = {}
CurrentTime = os.time()

RewardBtnImg	= "Quest/Quest_2009_07_23_BT.bmp"
CountImg		= "Quest/Quest_2009_07_23_Count.bmp"
ListBtnImg		= "Quest/Quest_2009_07_23_List.bmp"
BackImg			= "Quest/Quest_2009_07_23_Back.jpg"
EndImg			= "Quest/Quest_2009_07_23_Back_END.jpg"
EndRewardImg	= "Quest/Quest_2009_07_23_END_ITEM.bmp"

MonPenImg		= "Quest/Quest_2009_07_23_Mon00.bmp"
MonOctoImg		= "Quest/Quest_2009_07_23_Mon01.bmp"
MonSealImg		= "Quest/Quest_2009_07_23_Mon02.bmp"
MonRobotImg		= "Quest/Quest_2009_07_23_Mon03.bmp"

PenImgPosX		= 49
PenImgPosY		= 155

SealImgPosX		= 202
SealImgPosY		= 136

OctoImgPosX		= 59
OctoImgPosY		= 232

RobotImgPosX	= 212
RobotImgPosY	= 213

function OnShowQuest()
	AveragePoint		= 0
	
	if NumberData.Log5 ~= 0
	then
		if NumberData.Log5 == 1
		then
			AveragePoint = 100
		elseif NumberData.Log5 == 2
		then
			AveragePoint = 95
		elseif NumberData.Log5 == 3
		then
			AveragePoint = 90
		elseif NumberData.Log5 == 4
		then
			AveragePoint = 80
		elseif NumberData.Log5 == 5
		then
			AveragePoint = 70
		elseif NumberData.Log5 == 6
		then
			AveragePoint = 60
		end
	end

	AveragePoint_100	= math.mod(AveragePoint / 100, 10)
	AveragePoint_10		= math.mod(AveragePoint / 10 , 10)
	AveragePoint_1		= math.mod(AveragePoint      , 10) 

	NumberData.QuestBtn_Visible = 1
	StringData.QuestBtn_Path = ListBtnImg

	NumberData.Back_Visible = 1
	StringData.Back_Path = BackImg
	
	if NumberData.Log5 ~= 0
	then
		StringData.Back_Path = EndImg
		
		NumberData.Img_Count = 3 + 1
		StringData.Img00_Path = CountImg
		NumberData.Img00_Frame = AveragePoint_100
		NumberData.Img00_PosX = 172
		NumberData.Img00_PosY = 190
		StringData.Img01_Path = CountImg
		NumberData.Img01_Frame = AveragePoint_10
		NumberData.Img01_PosX = 194
		NumberData.Img01_PosY = 191
		StringData.Img02_Path = CountImg
		NumberData.Img02_Frame = AveragePoint_1
		NumberData.Img02_PosX = 216
		NumberData.Img02_PosY = 192
		
		
		StringData.Img03_Path = EndRewardImg
		NumberData.Img03_Frame = NumberData.Log5 - 1
		NumberData.Img03_PosX = 46
		NumberData.Img03_PosY = 238
	
	else
		NumberData.Img_Count = 4
		
		-- 0일 때 SS로 나오면 안되니까 랭크 로그 남길 때 + 1 해서 기록하고 여기선 1 빼준다
		StringData.Img00_Path = MonPenImg
		NumberData.Img00_Frame = NumberData.Log1 - 1
		NumberData.Img00_PosX = PenImgPosX
		NumberData.Img00_PosY = PenImgPosY
		
		StringData.Img01_Path = MonSealImg
		NumberData.Img01_Frame = NumberData.Log2 - 1
		NumberData.Img01_PosX = SealImgPosX
		NumberData.Img01_PosY = SealImgPosY

		StringData.Img02_Path = MonOctoImg
		NumberData.Img02_Frame = NumberData.Log3 - 1
		NumberData.Img02_PosX = OctoImgPosX
		NumberData.Img02_PosY = OctoImgPosY

		StringData.Img03_Path = MonRobotImg
		NumberData.Img03_Frame = NumberData.Log4 - 1
		NumberData.Img03_PosX = RobotImgPosX
		NumberData.Img03_PosY = RobotImgPosY
			
	end

	NumberData.IsSystemQuest = 1
	NumberData.UseDBString = 1
	StringData.QuestName = "MonRank_QuestName" -- 몬스터 모의고사


	if NumberData.Log5 ~= 0
	then
		return 0
	end

	NumberData.DoneBtn_Count = 1
	StringData.DoneBtn00_Path = RewardBtnImg
	NumberData.DoneBtn00_PosX = 97
	NumberData.DoneBtn00_PosY = 286

	if NumberData.Log1 ~= 0 and NumberData.Log2 ~= 0 and NumberData.Log3 ~= 0 and NumberData.Log4 ~= 0 and NumberData.Log5 == 0
	then
		NumberData.DoneBtn00_Visible = 1
	end
end

