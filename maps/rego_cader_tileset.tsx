<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2-2-geb83ddb9" name="rego_cader_tileset" tilewidth="64" tileheight="64" tilecount="12" columns="4">
 <image source="rego_cader_tileset.png" width="256" height="192"/>
 <tile id="0">
  <properties>
   <property name="type" value="cobblestone"/>
  </properties>
 </tile>
 <tile id="1">
  <properties>
   <property name="collision" value="true"/>
   <property name="type" value="wall"/>
  </properties>
 </tile>
 <tile id="2">
  <properties>
   <property name="collision" value="true"/>
   <property name="type" value="wall_window"/>
  </properties>
 </tile>
 <tile id="3">
  <properties>
   <property name="collision" value="true"/>
   <property name="type" value="wall_door"/>
  </properties>
 </tile>
 <tile id="4">
  <properties>
   <property name="collision" value="true"/>
   <property name="cover" value="true"/>
   <property name="type" value="barricade"/>
  </properties>
 </tile>
 <tile id="5">
  <properties>
   <property name="type" value="debris"/>
  </properties>
 </tile>
 <tile id="6">
  <properties>
   <property name="type" value="puddle"/>
  </properties>
 </tile>
 <tile id="7">
  <properties>
   <property name="type" value="shadow"/>
  </properties>
 </tile>
 <tile id="8">
  <properties>
   <property name="collision" value="true"/>
   <property name="type" value="rubble"/>
  </properties>
 </tile>
 <tile id="9">
  <properties>
   <property name="collision" value="true"/>
   <property name="type" value="wall_vine"/>
  </properties>
 </tile>
 <tile id="10">
  <properties>
   <property name="collision" value="true"/>
   <property name="cover" value="true"/>
   <property name="type" value="cart"/>
  </properties>
 </tile>
 <tile id="11">
  <properties>
   <property name="type" value="dirt"/>
  </properties>
 </tile>
 <wangsets>
  <wangset name="Рельефы" type="corner" tile="-1">
   <wangcolor name="Floor" color="#ff0000" tile="0" probability="1"/>
   <wangcolor name="Wall" color="#00ff00" tile="1" probability="1"/>
   <wangcolor name="Obstacle" color="#0000ff" tile="4" probability="1"/>
   <wangtile tileid="0" wangid="0,1,0,1,0,1,0,1"/>
   <wangtile tileid="1" wangid="0,2,0,2,0,2,0,2"/>
   <wangtile tileid="5" wangid="0,2,0,2,0,2,0,2"/>
   <wangtile tileid="8" wangid="0,3,0,3,0,3,0,3"/>
   <wangtile tileid="9" wangid="0,2,0,2,0,2,0,2"/>
   <wangtile tileid="11" wangid="0,3,0,3,0,3,0,3"/>
  </wangset>
 </wangsets>
</tileset>
